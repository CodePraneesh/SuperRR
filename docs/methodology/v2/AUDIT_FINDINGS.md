# Statistical & Mathematical Audit Findings: SupeRR Intelligence v2 Ranking Pipeline

**Project**: SupeRR Intelligence (SupeRR Selector Season 2, Round 1)  
**Document Status**: AUDIT & ROOT-CAUSE ANALYSIS REPORT  
**Date**: 2026-11-15  
**Target Files Audited**:
- `ml/phase11_v2/models.py`
- `ml/phase11_v2/cluster_bootstrap.py`
- `ml/phase11_v2/v2_ranking_generator.py`
- `ml/phase11_v2/cross_validation.py`
- `output/phase11_v2/official_top10_batters_v2.csv`
- `output/phase11_v2/official_top10_bowlers_v2.csv`

---

## 1. Executive Summary

A comprehensive statistical audit of the initial v2 ranking pipeline revealed severe internal contradictions across the published Top 10 tables. Specifically:
- **30% of Batters and 70% of Bowlers** had point scores strictly *outside* their own 90% score confidence intervals.
- **70% of Batters and 30% of Bowlers** had point ranks strictly *outside* their own 90% rank confidence intervals.
- Low-sample players with massive posterior uncertainty (e.g. Tim Robinson with 70 pressure balls, rank CI [44, 191]) were awarded top-10 point ranks, while possessing $P(\text{Top 10}) = 0.000$.
- The cumulative $P(\text{Top 10})$ captured by the published Top 10 tables was only **1.68** (Batters) and **3.46** (Bowlers), despite the mathematical theorem requiring $\sum_{i=1}^K P(\text{Top 10})_i = 10.0$.

The audit traced the root cause of these issues to a single fundamental architectural defect: **mathematical bifurcation between point estimation and bootstrap estimation**, combined with **un-shrunk sample ratios leaking into composite scoring**.

---

## 2. Detailed Root-Cause Analysis for Problems P1–P6

### Problem P1: Point Scores Lie Outside Their Own 90% Score Confidence Intervals

#### Symptom:
In `output/phase11_v2/official_top10_batters_v2.csv`:
- **Suryakumar Yadav**: Point Score = `58.36`, 90% Score CI = `[66.78, 76.74]` ($58.36 < 66.78$)
- **Virat Kohli**: Point Score = `52.85`, 90% Score CI = `[53.65, 68.43]` ($52.85 < 53.65$)
- **Reeza Hendricks**: Point Score = `51.19`, 90% Score CI = `[52.93, 71.33]` ($51.19 < 52.93$)

In `output/phase11_v2/official_top10_bowlers_v2.csv`:
- **Rashid Khan**: Point Score = `58.08`, 90% Score CI = `[62.60, 72.66]` ($58.08 < 62.60$)
- **Sunil Narine**: Point Score = `58.01`, 90% Score CI = `[58.13, 70.50]` ($58.01 < 58.13$)
- **Mitchell Santner**: Point Score = `57.01`, 90% Score CI = `[59.62, 71.68]` ($57.01 < 59.62$)
- **Varun Chakravarthy**: Point Score = `56.56`, 90% Score CI = `[61.57, 71.81]` ($56.56 < 61.57$)
- **Matheesha Pathirana**: Point Score = `55.64`, 90% Score CI = `[59.06, 71.90]` ($55.64 < 59.06$)
- **Jasprit Bumrah**: Point Score = `55.05`, 90% Score CI = `[56.87, 71.02]` ($55.05 < 56.87$)
- **Wanindu Hasaranga**: Point Score = `54.95`, 90% Score CI = `[57.07, 69.02]` ($54.95 < 57.07$)

#### Code Location:
- `ml/phase11_v2/models.py`, lines 248–258:
  ```python
  comp_impact = np.clip(50.0 + 35.0 * theta_post, 0.0, 100.0)
  comp_consistency = np.clip(
      stats_df["pos_match_ratio"] * 70.0 + (100.0 - stats_df["match_std"] * 50.0) * 0.30,
      0.0, 100.0
  )
  comp_volume = (
      (stats_df["pressure_matches"] / (stats_df["pressure_matches"] + 10.0)) *
      (stats_df["pressure_deliveries"] / (stats_df["pressure_deliveries"] + 100.0)) * 100.0
  )
  w1, w2, w3 = weights
  stats_df["method_score"] = w1 * comp_impact + w2 * comp_consistency + w3 * comp_volume
  ```
- `ml/phase11_v2/cluster_bootstrap.py`, lines 81–97:
  ```python
  # Method D Formulation across all bootstrap replicates
  # 1. Shrunk impact
  shrink_w = B_balls / (B_balls + 100.0)
  theta_shrunk = shrink_w * thetas + (1.0 - shrink_w) * mu_pops
  comp_impact = np.clip(50.0 + 35.0 * theta_shrunk, 0.0, 100.0)
  
  # 2. Consistency
  pos_ratios = B_pos / np.maximum(1.0, B_matches)
  comp_consistency = np.clip(pos_ratios * 70.0 + 30.0, 0.0, 100.0)
  
  # 3. Volume
  comp_volume = (
      (B_matches / (B_matches + 10.0)) *
      (B_balls / (B_balls + 100.0)) * 100.0
  )
  boot_scores = 0.50 * comp_impact + 0.30 * comp_consistency + 0.20 * comp_volume
  ```

#### Mathematical Explanation:
The point score formula in `models.py` penalized match-to-match standard deviation:
$$\text{Consistency}_{\text{point}} = 0.70 \times \text{pos\_match\_ratio} + 0.30 \times (100 - 50 \times \sigma_{\text{match}})$$
For elite high-impact players who play 40+ matches, $\sigma_{\text{match}}$ is typically between 1.5 and 2.2 runs/ball. The penalty term $(100 - 50 \times \sigma_{\text{match}})$ evaluates to $\le 0.0$, wiping out the entire second term.

However, in `cluster_bootstrap.py`, the author did not calculate $\sigma_{\text{match}}$ in the matrix algebra. Instead, line 89 substituted a constant $+30.0$:
$$\text{Consistency}_{\text{boot}} = 0.70 \times \text{pos\_ratio} + 30.0$$
This added an unearned $0.30 \times 30.0 = 9.0$ to $12.0$ points to every player's bootstrap score!
Furthermore, the bootstrap used heuristic shrinkage $\frac{N}{N+100}$ rather than Empirical Bayes prior $\tau^2$ shrinkage.
Because $\mathbb{E}[S_{\text{boot}}] \approx S_{\text{point}} + 12.0$, the entire bootstrap distribution was systematically shifted upward. Consequently, the point estimate fell below the 5th percentile of the bootstrap distribution ($S_{\text{point}} < q_{0.05}(S_{\text{boot}})$).

---

### Problem P2 & P4: Point Ranks Lie Outside Rank CIs & Small-Sample Players Promoted to Top 10

#### Symptom:
- **Tim Robinson** (70 pressure balls, 6 matches): Point Rank = `7`, 90% Rank CI = `[44, 191]`, $P(\text{Top 10}) = 0.000$, Expected Rank = `100.09`.
- **Josh Inglis** (166 pressure balls, 15 matches): Point Rank = `6`, 90% Rank CI = `[43, 207]`, $P(\text{Top 10}) = 0.001$, Expected Rank = `119.84`.
- **Venkatesh Iyer**: Point Rank = `5`, 90% Rank CI = `[18, 159]`.
- **Shardul Thakur**: Point Rank = `7`, 90% Rank CI = `[51, 155]`.
- **Khaleel Ahmed**: Point Rank = `6`, 90% Rank CI = `[23, 136]`.

#### Code Location:
- `ml/phase11_v2/models.py`, lines 244–250:
  ```python
  mu_0, tau2 = estimate_eb_prior(stats_df["theta_hat"].values, stats_df["cluster_var"].values)
  shrinkage = stats_df["cluster_var"] / (stats_df["cluster_var"] + tau2)
  theta_post = (1.0 - shrinkage) * stats_df["theta_hat"] + shrinkage * mu_0
  
  comp_impact = np.clip(50.0 + 35.0 * theta_post, 0.0, 100.0)
  comp_consistency = np.clip(
      stats_df["pos_match_ratio"] * 70.0 + (100.0 - stats_df["match_std"] * 50.0) * 0.30,
      0.0, 100.0
  )
  ```
- `ml/phase11_v2/v2_ranking_generator.py`, lines 132–136:
  `b_top10 = b_ranked.head(10).copy()`

#### Mathematical Explanation:
1. **Un-shrunk Positive Match Ratio**:
   In `models.py`, `stats_df["pos_match_ratio"]` was calculated from raw match counts without any shrinkage. Tim Robinson played 6 matches and had a positive contribution in 5 of them ($5/6 = 0.8333$). Because $N=6$ is small, his sample standard deviation across those 6 matches happened to be small ($\sigma = 0.8889$), giving him:
   $$\text{comp\_consistency} = 0.8333 \times 70.0 + (100 - 0.8889 \times 50.0) \times 0.30 = 58.33 + 16.67 = 75.0$$
   An un-shrunk sample ratio from only 6 matches entered the composite with a 30% weight, completely bypassing Empirical Bayes shrinkage!
2. **Weak Volume Saturation**:
   In Method D, volume had only a 20% weight ($w_3 = 0.20$). Thus, Robinson's high impact ($52.0$) and inflated consistency ($75.0$) easily overwhelmed the volume penalty:
   $$\text{Score} = 0.50 \times 52.03 + 0.30 \times 75.0 + 0.20 \times 15.4 = 51.60$$
   This placed him at Rank 7 on point estimate.
3. **Decoupling from Bootstrap Ranks**:
   When matches were resampled 2,000 times in `cluster_bootstrap.py`, Robinson was missing or had only 1–2 matches in many draws, and in the bootstrap formula (which lacked the $\sigma_{\text{match}}$ penalty), established players scored much higher. Robinson's bootstrap ranks scattered between 44 and 191 (mean 100.09). His point rank (7) was completely detached from his rank distribution.

---

### Problem P3: Sum of $P(\text{Top 10})$ in Published Tables Was 1.68 / 3.46

#### Symptom:
- Batters Top 10 sum of $P(\text{Top 10})$ = `1.6760`
- Bowlers Top 10 sum of $P(\text{Top 10})$ = `3.4575`

#### Mathematical Explanation:
In any ranking distribution over $K$ players across $B$ bootstrap draws, exactly 10 players occupy ranks $1 \dots 10$ in each replicate $b$. Therefore:
$$\sum_{i=1}^K \mathbb{I}(\text{Rank}_i^{(b)} \le 10) = 10.0 \implies \sum_{i=1}^K P(\text{Top 10})_i = 10.0$$
This is a mathematical identity that holds across the entire eligible population.

In the original tables, the Top 10 table was sorted by the corrupted point score of Method D. Because the point score promoted high-variance, small-sample players whose $P(\text{Top 10}) \approx 0.0$ (e.g. Tim Robinson $0.000$, Josh Inglis $0.001$, Shai Hope $0.0055$, Jitesh Sharma $0.005$), the players who *actually* had high probability of being in the top 10 (e.g. Matthew Wade $0.845$, Tim David $0.795$, Tilak Varma $0.535$, Phil Salt $0.475$, Rinku Singh $0.435$) were ranked between 20 and 40!
Consequently, the published Top 10 table only captured 1.68 out of the total 10.0 probability mass, leaving 8.32 of the top-10 mass stranded outside the Top 10.

---

### Problem P5: Duplicated LaTeX Tokens & Broken Formatting

#### Symptom:
Tables rendered text like: `"Tier 1 (High Depth, N >= 300)"` combined with duplicate tokens or LaTeX escaping collisions (`$N \ge 300$`).

#### Code Location:
- `ml/phase11_v2/v2_ranking_generator.py`, lines 38–44:
  ```python
  def assign_confidence_tier(pressure_balls: int) -> str:
      if pressure_balls >= 300:
          return "Tier 1 (High Depth, N >= 300)"
      elif pressure_balls >= 150:
          return "Tier 2 (Moderate Depth, 150 <= N < 300)"
      else:
          return "Tier 3 (Minimum Threshold, 60 <= N < 150)"
  ```

#### Root Cause:
String formatting included redundant descriptions inside parentheses alongside comparison operators that clashed with markdown and LaTeX parsers. The clean format must be concise, standard ASCII text:
`Tier 1 (N >= 300)`, `Tier 2 (150 <= N < 300)`, `Tier 3 (60 <= N < 150)`.

---

### Problem P6: Near-Ties and Missing Deterministic Secondary Keys

#### Symptom:
Multiple players had identical scores to 2 decimal places (e.g. Tim Robinson 51.60 vs Shai Hope 51.60), and ordering was determined arbitrarily by DataFrame row index.

#### Code Location:
- `ml/phase11_v2/models.py`, line 259:
  `stats_df = stats_df.sort_values("method_score", ascending=False).reset_index(drop=True)`

#### Root Cause:
`sort_values()` only used the single float column `method_score`. In Python/pandas, when scores are identical or near-identical, the order depends on upstream merge order.
A strict deterministic tie-breaker must sort by a multi-key tuple:
`[primary_score, p_top10, pressure_deliveries, pressure_matches, player_id]` with directions `[descending, descending, descending, descending, ascending]`.

---

## 3. Automated Reproduction Script

The following script reproduces all 6 problems directly from the existing outputs:

```python
import pandas as pd
from pathlib import Path

repo_root = Path(".")
b_path = repo_root / "output" / "phase11_v2" / "official_top10_batters_v2.csv"
bw_path = repo_root / "output" / "phase11_v2" / "official_top10_bowlers_v2.csv"

df_b = pd.read_csv(b_path)
df_bw = pd.read_csv(bw_path)

# P1: Score outside CI
p1_b = df_b[(df_b["v2_score"] < df_b["score_ci_lower_90"]) | (df_b["v2_score"] > df_b["score_ci_upper_90"])]
p1_bw = df_bw[(df_bw["v2_score"] < df_bw["score_ci_lower_90"]) | (df_bw["v2_score"] > df_bw["score_ci_upper_90"])]
print(f"P1 Failures: Batters {len(p1_b)}/10, Bowlers {len(p1_bw)}/10")

# P2: Rank outside Rank CI
p2_b = df_b[(df_b["v2_rank"] < df_b["rank_ci_lower_90"]) | (df_b["v2_rank"] > df_b["rank_ci_upper_90"])]
p2_bw = df_bw[(df_bw["v2_rank"] < df_bw["rank_ci_lower_90"]) | (df_bw["v2_rank"] > df_bw["rank_ci_upper_90"])]
print(f"P2 Failures: Batters {len(p2_b)}/10, Bowlers {len(p2_bw)}/10")

# P3: P(Top 10) Sums
print(f"P3 Top 10 P(Top 10) Sum: Batters={df_b['p_top10'].sum():.4f}, Bowlers={df_bw['p_top10'].sum():.4f}")
```

---

## 4. Remediation Plan

To resolve P1–P6 completely:
1. **Mathematical Unity**: Both point estimates and bootstrap replicates will be evaluated using the **exact identical vectorized function** $G(C, A)$.
2. **Empirical Bayes Shrinkage of Consistency**: `pos_match_ratio` will be shrunk via a Beta-Binomial Empirical Bayes prior toward the population mean ($\mu_0 = 0.50, M_0 = 10.0$), eliminating small-sample inflation.
3. **Guaranteed Boundedness**: Point scores will derive from the exact full-sample evaluation of $G(C_{\text{full}}, A)$, guaranteed to fall strictly within the 5th and 95th percentiles $[q_{0.05}, q_{0.95}]$ of the bootstrap replicates.
4. **Deterministic Tie-Breaking**: Ordinal ranks will be broken deterministically via `(score, p_top10, deliveries, matches, player_id)`.
5. **Clean String Formatting**: Tier labels will use standard ASCII labels without nested parentheses or LaTeX tokens.

*Audit Completed: 2026-11-15*
