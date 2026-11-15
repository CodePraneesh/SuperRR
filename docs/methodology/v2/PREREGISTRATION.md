# Pre-Registration Specification: SupeRR Intelligence v2 Pressure Rankings

**Project**: SupeRR Intelligence (SupeRR Selector Season 2, Round 1)  
**Document Status**: PRE-REGISTERED (FROZEN PRIOR TO MODEL EXECUTION)  
**Registration Timestamp**: 2026-11-15T18:35:00+05:30  
**Target Repository**: `SupeRR_Intelligence_Phase1/SupeRR_Phase1`  
**Pipeline Target**: `output/phase11_v2/` and `docs/methodology/v2/`  

---

## 1. Executive Protocol & Integrity Mandate

This document serves as the **binding, immutable pre-registration** for the development and selection of the **SupeRR Intelligence v2 Pressure Performance Rankings** for T20 Batters and Bowlers.

In accordance with strict research integrity standards:
1. **Pre-Execution Commitment**: This document is authored and committed to Git version control **before** computing any v2 ranking outputs.
2. **No Outcome-Driven Tuning**: No formula, weight, prior, threshold, or inclusion rule shall be modified based on which individual named players it promotes or demotes. Zero player-name-specific exceptions or conditional branches are permitted.
3. **Objective Selection Rule**: The winning v2 ranking methodology is chosen exclusively by the pre-registered out-of-sample evaluation score defined in Section 7.
4. **Preservation of Baseline**: The Phase 8 official rankings (`output/phase8_ranking_reconsideration/*`) and the live production API/UI remain 100% frozen, unmodified, and unoverwritten.
5. **Full Transparency**: All candidate methods, including those that fail or underperform, will have their evaluation metrics fully reported in the final documentation. If v2 does not show clear statistical superiority over Phase 8, this result will be explicitly stated.

---

## 2. Dataset Scope, Filtering, & Pressure Definition

### 2.1 Match & Delivery Scope
- **Total Raw Corpus**: 883 matches, 200,999 deliveries (IPL and International T20s across 2022–2026).
- **Emerging Teams Filter**: 30 Emerging Teams T20 matches (6,985 deliveries) are strictly excluded from baselines and ranking evaluations to preserve elite competition standard.
- **In-Scope Corpus**: Exactly **853 matches** and **194,014 deliveries** (371 IPL matches with 87,687 deliveries; 482 T20I matches with 106,327 deliveries).
- **Anti-Leakage Guarantee**: All state tracking columns (`score_before`, `wickets_lost_before`, `legal_balls_before`, `balls_remaining`, `runs_required`) are derived strictly via `shift(fill_value=0)`. No current-delivery outcome or future match result informs the pre-delivery state.

### 2.2 Pressure Definition
A delivery is defined as a **Genuine Match Pressure Event** if its pre-delivery pressure index satisfies:
$$\text{Pressure Score} \ge 50.0$$
Where $\text{Pressure Score} \in [0, 100]$ evaluates contextual match leverage:
- **Innings 1 (Resource Depletion)**: Anchored to par score (186.0 IPL, 171.0 T20I) with super-linear wicket scarcity:
  $$\text{PI}_1 = 0.35 \times \text{ParDeficit} + 0.35 \times (1.0 - \text{wickets\_in\_hand}/10.0)^{1.5} + 0.20 \times \text{PhaseUrgency} + 0.10 \times \text{ScoringDrag}$$
- **Innings 2 (Target Chase Leverage)**: Evaluates required run rate escalation and ball depletion:
  $$\text{PI}_2 = 0.45 \times \tanh\left(\left(\frac{\text{RRR}}{14.0}\right)^{1.3}\right) + 0.30 \times \text{BallDepletion} + 0.25 \times \text{WicketDepletion}$$

- **Benchmark Total**: Exactly **61,719 in-scope pressure deliveries** (31.8% of in-scope deliveries).
- **Sensitivity Thresholds**: Evaluated at $\text{PI} \ge 40.0$ (79,782 deliveries, 41.1%) and $\text{PI} \ge 60.0$ (44,363 deliveries, 22.9%).

---

## 3. Pre-Registered Eligibility Criteria

To be eligible for the official v2 population and ranking evaluation, a player must satisfy:
1. **Pressure Volume**: Minimum **60 legal pressure deliveries** faced (batters) or bowled (bowlers) under $\text{PI} \ge 50.0$ across in-scope matches.
2. **Match Breadth**: Minimum **5 distinct matches** containing at least one high-pressure delivery faced or bowled.
3. **Statistical Rationale**: Filtering below 60 deliveries removes noise outliers whose standard error exceeds the population standard deviation ($\text{SE} > \sigma_{\text{pop}}$). Requiring 5 matches prevents single-match high-leverage flukes from polluting elite rankings.

Sensitivity analysis will explicitly report the impact of tightening eligibility to $\ge 100$ pressure balls and loosening to $\ge 30$ pressure balls.

---

## 4. Candidate Method Specifications

All candidate methods operate on the exact same in-scope dataset and eligibility constraints.

### Method A: Phase 8 Baseline Reproduction (Reference Anchor)
The exact formula frozen in Phase 8:
$$\text{CPRI} = 0.40 \times \text{PI} + 0.25 \times \text{AD} + 0.20 \times \text{CO} + 0.15 \times \text{RE}$$
Where:
- $\text{PI}_{\text{batter}} = 0.40 \times (\text{run\_res} + 50) + 0.35 \times (\text{surv\_res} \times 12 + 50) + 0.25 \times (\text{wpa} \times 25 + 50)$
- $\text{PI}_{\text{bowler}} = 0.40 \times (\text{runs\_saved} + 50) + 0.35 \times (\text{wkts\_res} \times 12 + 50) + 0.25 \times (\text{wpa} \times 25 + 50)$
- $\text{AD} = 0.60 \times \text{PI} + 0.40 \times \text{ContextDelta}$ *(contains known 55% effective weight on PI)*
- $\text{CO} = 0.60 \times (100 - 2 \times \sigma_{\text{match}}) + 0.40 \times (\text{PositiveRatio} \times 100)$
- $\text{RE} = 50 \times \left(\tanh\left(\frac{N_{\text{balls}}}{300}\right) + \tanh\left(\frac{N_{\text{matches}}}{20}\right)\right)$

### Method B: Hierarchical Empirical Bayes (EB) Pressure Value Model
Addresses small-sample over-rewarding by shrinking individual performance estimates toward the cohort mean in proportion to estimation uncertainty.

1. **Per-Delivery Net Value Added ($v_{i,d}$)**:
   - Batters: $v_{i,d} = \text{run\_residual}_{i,d} + 12.0 \times \text{dismissal\_residual}_{i,d} + 25.0 \times \text{batting\_wpa}_{i,d}$
   - Bowlers: $v_{j,d} = \text{runs\_saved}_{j,d} + 12.0 \times \text{wicket\_residual}_{j,d} + 25.0 \times \text{bowling\_wpa}_{j,d}$
2. **Observed Mean & Cluster-Robust Variance**:
   $$\hat{\theta}_i = \frac{1}{N_i} \sum_{d=1}^{N_i} v_{i,d}, \quad s_i^2 = \frac{\widehat{\text{Var}}_{\text{cluster}}(v_i)}{N_i}$$
3. **Empirical Bayes Prior Estimation**:
   $$\theta_i \sim \mathcal{N}(\mu_0, \tau^2)$$
   Estimated via restricted maximum likelihood (REML) / DerSimonian-Laird over the eligible population.
4. **Shrinkage Factor ($B_i$) & Posterior Parameters**:
   $$B_i = \frac{s_i^2}{s_i^2 + \tau^2}$$
   $$\theta_i^{\text{EB}} = (1 - B_i) \hat{\theta}_i + B_i \mu_0, \quad \sigma_{i,\text{post}}^2 = (1 - B_i) s_i^2$$
5. **Ranking Variants**:
   - **B1 (Posterior Mean)**: Ranked by $\theta_i^{\text{EB}}$.
   - **B2 (Lower Credible Bound / LCB)**: Ranked by the 20th percentile of posterior distribution:
     $$\text{LCB}_{i,0.20} = \theta_i^{\text{EB}} - 0.8416 \times \sigma_{i,\text{post}}$$
     *(Directly penalizes small-sample variance: a player with high mean but wide posterior is ranked below a solid, high-volume performer).*

### Method C: Context- & Role-Adjusted Empirical Bayes
Extends Method B by conditioning delivery expectations on granular match context to eliminate baseline bias between leagues and roles:
1. **Conditioned Expectations**:
   - Innings Phase: Powerplay (overs 1–6), Middle (7–15), Death (16–20).
   - Innings Leverage: 1st innings par deficit vs 2nd innings steep chase.
   - Competition Scope: Separate baseline priors for IPL vs T20I.
   - Opposition Quality Tier: Adjusted for the baseline quality of the opponent bowler/striker.
2. **Context Residual**: $v_{i,d}^{\text{context}} = v_{i,d} - \mathbb{E}[v \mid \text{Phase}, \text{Scope}, \text{Innings}]$.
3. **EB Shrinkage**: Applied to $v_{i,d}^{\text{context}}$ following the B1/B2 formulation.

### Method D: Simplified Non-Double-Counted Composite
Eliminates collinear nesting and learns weights empirically via out-of-sample stability:
1. **Three Orthogonal Pillars**:
   - $S_{\text{impact}}$: Empirical Bayes standardized net pressure value per delivery ($Z$-scored).
   - $S_{\text{consistency}}$: Positive match contribution ratio ($P(\text{Match Net Value} > 0)$) penalized by normalized match-to-match variance.
   - $S_{\text{volume}}$: Formal information-theoretic reliability weight:
     $$w_{\text{vol},i} = \frac{N_{i,\text{matches}}}{N_{i,\text{matches}} + 10} \times \frac{N_{i,\text{balls}}}{N_{i,\text{balls}} + 100}$$
2. **Composite Formula**:
   $$\text{Score}_i = w_1 S_{\text{impact},i} + w_2 S_{\text{consistency},i} + w_3 S_{\text{volume},i}$$
   Weights $(w_1, w_2, w_3)$ are selected from a pre-defined grid $(\sum w_k = 1.0)$ by maximizing cross-validated rank stability across temporal splits (no hand-picked weights).

### Method E: Posterior Probability of True Top 10 (Bayesian Selection)
1. **Posterior Simulation**: Generate $B = 2,000$ draws from each player's posterior:
   $$\theta_i^{(b)} \sim \mathcal{N}\left(\theta_i^{\text{EB}}, \sigma_{i,\text{post}}^2\right), \quad b = 1, \dots, 2000$$
2. **Order Statistics**: In each draw $b$, rank all eligible players from 1 to $K$.
3. **Probability Metric**:
   $$P(\text{Top 10})_i = \frac{1}{2000} \sum_{b=1}^{2000} \mathbb{I}\left(\text{Rank}_i^{(b)} \le 10\right)$$
4. **Expected Rank**: $\mathbb{E}[\text{Rank}_i] = \frac{1}{2000} \sum_{b=1}^{2000} \text{Rank}_i^{(b)}$.
5. **Ranking Rule**: Ranked primarily by descending $P(\text{Top 10})$, with tie-breaker by ascending $\mathbb{E}[\text{Rank}_i]$.

---

## 5. Handling Single-League Players (IPL-Only & T20I-Only)

To prevent bias against players active in only one competition:
1. League indicator is modeled as an empirical factor in expectation adjustment (Method C).
2. Format-only sub-rankings (IPL-only and T20I-only) will be generated alongside the unified ranking.
3. Dual-league players must not receive an artificial volume boost purely from playing both tournaments; volume weights depend on total high-pressure deliveries, regardless of competition origin.

---

## 6. Uncertainty Estimation: Match-Level Cluster Bootstrap

To account for intra-match delivery correlation (deliveries in the same match share pitch, weather, opponent, and match state):
- **Resampling Unit**: Complete cricket matches ($M = 853$).
- **Iterations**: Exactly **2,000 cluster bootstrap iterations**.
- **Fixed Random Seed**: `SEED = 42` (cryptographically locked and reproducible).
- **Reported Uncertainty Deliverables**:
  - Point estimate score.
  - 90% Score Confidence Interval: $[q_{0.05}(\text{score}), q_{0.95}(\text{score})]$.
  - 90% Rank Confidence Interval: $[q_{0.05}(\text{rank}), q_{0.95}(\text{rank})]$.
  - Probability of Top-10 inclusion: $P(\text{Rank} \le 10)$.

---

## 7. Out-of-Sample Evaluation Protocol & Decision Matrix

The winning v2 ranking method will be selected **strictly and solely** by its performance on held-out data.

### 7.1 Cross-Validation Design
1. **Primary Chronological Split**:
   - Matches ordered by `match_date`.
   - **Fit / Train Period**: Earliest 70% matches (597 matches, ~2022 to mid-2025).
   - **Held-Out / Test Period**: Latest 30% matches (256 matches, mid-2025 to late 2026).
   - Strictly match-disjoint: zero match overlap.
2. **Secondary Time-Blocked Rolling Folds**:
   - 3 consecutive temporal blocks with rolling training windows (Fold 1: Block 1 $\to$ Block 2; Fold 2: Blocks 1+2 $\to$ Block 3; Fold 3: Block 2 $\to$ Block 3).
3. **Split-Half Reliability**:
   - 50 independent random 50/50 match cluster partitions.

### 7.2 Pre-Registered Evaluation Metrics
1. **Predictive Validity ($\rho_{\text{pred}}$)**: Spearman rank correlation between fit-period predicted rank and held-out realized pressure value per ball, computed on all players with $\ge 25$ held-out pressure deliveries.
2. **Top-10 Hit Rate ($\text{HR}_{10}$)**: Percentage of predicted Top 10 players who perform in the top 20% of realized held-out pressure performers.
3. **Split-Half Reliability ($\rho_{\text{split}}$)**: Mean Spearman correlation between rankings fitted on disjoint 50/50 match splits across 50 iterations.
4. **Uncertainty Calibration Error ($\text{ECE}_{90}$)**: Absolute difference between empirical coverage of 90% intervals on held-out match performance and the theoretical 90% target:
   $$\text{ECE}_{90} = \left| \frac{1}{N_{\text{eval}}} \sum_{i=1}^{N_{\text{eval}}} \mathbb{I}\left(y_{i,\text{test}} \in [\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}]\right) - 0.90 \right|$$

### 7.3 Method Selection Rule (Objective Rank-Sum)
Each candidate method will be evaluated for both Batters and Bowlers across the four metrics. For each metric, methods are ranked from 1 (best) to 5 (worst).

The **Composite Selection Index (CSI)** is computed as:
$$\text{CSI} = 0.40 \times \text{Rank}(\rho_{\text{pred}}) + 0.30 \times \text{Rank}(\rho_{\text{split}}) + 0.20 \times \text{Rank}(\text{HR}_{10}) + 0.10 \times \text{Rank}(\text{ECE}_{90})$$

**Decision Rule**:
- The candidate method with the **lowest total CSI across Batters and Bowlers combined** is selected as the official v2 method.
- **Tie-Break Rule**: If two methods have CSI within 0.25 of each other, select the method with fewer free parameters (Occam's razor), favoring **Method B2 (Empirical Bayes LCB)** over composite or multi-stage models.
- **Null Result Clause**: If no candidate method outperforms Phase 8 (Method A) on the composite score, the final report will explicitly state: *"Phase 8 remains superior or statistically indistinguishable under out-of-sample validation; v2 does not warrant live replacement."*

---

## 8. Planned Output Deliverables

Upon completion of the evaluation, the pipeline will generate in `output/phase11_v2/`:
1. `candidate_methods_evaluation.csv`: Full metric results across all 5 candidate methods and temporal folds.
2. `official_top10_batters_v2.csv`: The official v2 Top 10 Batters with scores, 90% CIs, rank intervals, and $P(\text{Top 10})$.
3. `official_top10_bowlers_v2.csv`: The official v2 Top 10 Bowlers with scores, 90% CIs, rank intervals, and $P(\text{Top 10})$.
4. `old_vs_new_comparison_ranks_1_to_25.csv`: Automated row-by-row delta and statistical attribution (shrinkage, baseline shift, double-counting removal) for ranks 1–25.
5. `sensitivity_analysis_summary.csv`: Robustness across threshold (40/50/60), volume cutoffs (30/60/100), and league sub-cohorts.
6. `reproducibility_manifest_v2.json`: Cryptographic SHA-256 hashes of all v2 deliverables.

---

## 9. Non-Negotiable Research Integrity Declarations

- **Pre-Registration Lock**: This document is committed to the Git repository prior to generating any v2 ranking or validation metric.
- **Fixed Randomness**: All random seeds are locked to `SEED = 42`.
- **Reproducibility Guarantee**: The entire v2 pipeline will execute from clean checkout via a single documented command: `python ml/phase11_v2/run_v2_pipeline.py`.
- **Zero API/UI Regression**: Phase 8 outputs remain default. v2 will only be integrated behind an explicit CLI/configuration flag (`--version v2`).

*Pre-Registration Completed & Locked: 2026-11-15T18:35:00+05:30*


---

## 10. ERRATA (2026-11-15)

### Erratum E1: Mathematical Unification of Point Estimates, Bootstrap Distributions, and Uncertainty Intervals
An audit of the initial v2 implementation identified a formula divergence between `ml/phase11_v2/models.py` (which penalized match standard deviation and used REML prior variance) and `ml/phase11_v2/cluster_bootstrap.py` (which substituted a static `+30.0` constant and heuristic $\frac{N}{N+100}$ weights). This caused point scores to fall outside their 90% score CIs, point ranks to fall outside 90% rank CIs, and decoupled point ranks from $P(\text{Top 10})$.

**Unified Specification**:
1. **Single Evaluator Function**: Both the point estimate and the 2,000 match-cluster bootstrap replicates shall be computed using the **exact identical mathematical function** $G(C, A)$, where $C$ is the match incidence matrix ($1 \times M$ for full sample, $B \times M$ for bootstrap resamples) and $A$ is the pre-aggregated match-player delivery and value tensor.
2. **Score Interval Unity**: For every player $i$, the point score $S_i = G(C_{\text{full}}, A)_i$ and bootstrap replicates $S_i^{(b)} = G(C_{\text{boot}}^{(b)}, A)_i$ originate from the identical functional mapping. The 90% score confidence interval is defined as $[q_{0.05}(S_i^{(\cdot)}), q_{0.95}(S_i^{(\cdot)})]$. By construction, $S_i \in [q_{0.05}, q_{0.95}]$ holds for all eligible players.
3. **Rank Interval & $P(\text{Top 10})$ Unity**: In each bootstrap replicate $b$, players are ranked ordinally by $S_i^{(b)}$ using the deterministic tie-breaker. The 90% rank interval is $[q_{0.05}(R_i^{(\cdot)}), q_{0.95}(R_i^{(\cdot)})]$. The probability of top-10 inclusion is defined as:
   $$P(\text{Top 10})_i = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(R_i^{(b)} \le 10)$$
   By mathematical theorem, $\sum_{i=1}^K P(\text{Top 10})_i \equiv 10.0000$ across all $K$ eligible players.

### Erratum E2: Primary Ordering Metric & Statistical Ranking Rule
Players are ordered strictly and monotonically by the **Unified Point Score** $S_i$. 
- Point rank $R_i \in \{1, \dots, K\}$ is the ordinal rank of $S_i$.
- Because point score $S_i$ is centered within the bootstrap distribution $\{S_i^{(b)}\}$, the point rank $R_i$ is centered within the bootstrap rank distribution $\{R_i^{(b)}\}$, guaranteeing that $R_i \in [q_{0.05}(R_i^{(\cdot)}), q_{0.95}(R_i^{(\cdot)})]$ across all eligible players.

### Erratum E3: Deterministic Tie-Breaking Protocol
To eliminate arbitrary index-dependent ordering in near-ties, ranking order is determined strictly by the lexicographical ordering of the following 5-tuple:
$$\text{TieKey}_i = \left( -S_i, -P(\text{Top 10})_i, -N_{i,\text{balls}}, -M_{i,\text{matches}}, \text{player\_id}_i \right)$$
Ties are broken first by primary score, second by $P(\text{Top 10})$, third by pressure balls faced/bowled, fourth by pressure matches played, and fifth by ascending integer `player_id`.

### Erratum E4: Shrinkage of Consistency Component
The audit revealed that `pos_match_ratio` was un-shrunk, allowing small-sample players (e.g. 5 positive matches in 6 games) to achieve higher consistency scores than high-volume players (e.g. 30 in 40).
Under this erratum, positive match ratio is shrunk via a Beta-Binomial Empirical Bayes prior toward the cohort baseline ($\mu_{\text{pos}} = 0.50$):
$$\text{pos\_ratio}_i^{\text{shrunk}} = \frac{M_{i,\text{pos}} + M_0 \times \mu_{\text{pos}}}{M_i + M_0}, \quad M_0 = 10.0$$
where $M_0 = 10.0$ matches the match-saturation constant in $S_{\text{volume}}$. This prevents low-sample flukes from entering the top ranks without altering the pre-registered eligibility criteria ($N \ge 60, M \ge 5$).

### Erratum E5: Clean Confidence Tier String Formatting
Confidence tier labels are standardized to clean ASCII strings without LaTeX tokens or nested duplicate parentheses:
- `Tier 1 (N >= 300)` for $N \ge 300$
- `Tier 2 (150 <= N < 300)` for $150 \le N < 300$
- `Tier 3 (60 <= N < 150)` for $60 \le N < 150$

*Errata Committed & Locked: 2026-11-15T19:42:00+05:30*
