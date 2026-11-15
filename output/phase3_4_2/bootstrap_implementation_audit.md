# SupeRR Intelligence — Phase 3.4.2 Bootstrap Implementation & Consistency Audit

## 1. Audit Overview & Verified Implementation Characteristics

This document provides a complete audit of the resampling methodology, reconciling all internal contradictions identified in the Phase 3.4.1 report.

### Implementation Audit Checklist:
- **Resampling Unit**: Match-level clustered deliveries (independent draws of entire match records) vs Tournament-cluster resampling.
- **Duplicate Match Handling**: Match records are weighted multiplicatively according to integer draw frequencies $k_m \in \{0, 1, 2, \dots\}$, strictly preserving ball-by-ball intra-match dependencies.
- **Cluster Definitions**:
  * **IPL**: 5 annual tournament editions (`2022`, `2023`, `2024`, `2025`, `2026`).
  * **T20I**: 49 monthly series windows (`YYYY-MM`) reflecting bilateral tours and ICC tournaments.
- **Random Seed**: Fixed at `42` (`np.random.seed(42)`) for 100% deterministic reproducibility.
- **Number of Iterations**: Exactly `1,000` Monte Carlo iterations per cohort and design ($8,000$ total full-pipeline evaluations).
- **Missing / Ineligible Players**: Evaluated explicitly under both conditional distributions ($N \mid \text{Eligible}$) and unconditional distributions ($N / N_{\text{iterations}}$).

## 2. Reconciling Rank Probability vs. Rank Interval

### The Root Cause of the Contradiction:
In Phase 3.4.1, `rank1_probability_pct` was computed **unconditionally** ($N_{\text{rank}=1} / N_{\text{total}}$), whereas `rank_95_interval` was computed **conditionally** over only the surviving iterations where the player met eligibility criteria.

### Verified Mathematical Reconciliation (Matthew Wade Example):
- In T20I tournament resampling, Matthew Wade qualified in **71.8% of iterations**.
- In **every single iteration where he qualified, his rank was 1**.
- **Conditional Rank Interval (given qualification)**: `[1, 1]` (since all conditional draws are 1).
- **Unconditional Rank Interval (assigning unranked/ineligible penalty)**: `[1, 79]` (capturing the 28.2% of draws where his matches were omitted).
- Both metrics are now explicitly separated in `bootstrap_rank_distribution.csv` with zero ambiguity.

## 3. Cohort-Wide Match vs. Tournament SE Comparison

### Empirical Findings Across All Qualified Players:

| cohort | total_players | players_se_increased | players_se_decreased | mean_match_se | mean_tourn_se | mean_pct_change |
| --- | --- | --- | --- | --- | --- | --- |
| IPL Batters | 88 | 18 | 70 | 9.214659090909091 | 7.373522727272728 | -19.58943181818182 |
| IPL Bowlers | 82 | 24 | 58 | 8.968658536585366 | 7.207195121951219 | -19.125365853658536 |
| T20I Batters | 88 | 21 | 67 | 9.539545454545454 | 8.301136363636363 | -11.680909090909092 |
| T20I Bowlers | 89 | 21 | 68 | 9.780898876404494 | 8.827415730337078 | -9.588651685393259 |

### Statistical Interpretation:
1. **T20I Batters and Bowlers**: With 49 monthly series clusters, tournament clustering genuinely reflects series-level variance. Uncertainty shifts realistically according to player participation patterns.
2. **IPL Coarse Season Effect**: Because IPL contains only 5 large clusters (74 matches each), resampling 5 seasons monolithic blocks suppresses within-season delivery variation for players active in only 1–2 seasons. This explains why conditional SE dropped for players like Rinku Singh.

## 4. Root Cause of Bootstrap Mean Drops

The drop between deterministic baseline CPRI and bootstrap mean CPRI is caused by three distinct factors:
1. **Outlier Maxima Inflation**: In bootstrap draws, small-sample players who hit high strike rates in a single match can generate extreme $s_{\max}$ values if that match is sampled multiple times, compressing the min-max scores of established players.
2. **Consistency Proxy**: Phase 3.4.1 used a simplified proxy for consistency which had a lower mean than the exact Phase 3.3 multi-component formula.
3. **Jensen's Inequality on Sigmoid**: The nonlinear transformation $f(E[Z]) \neq E[f(Z)]$ produces slight concave dampening at the high tail.
