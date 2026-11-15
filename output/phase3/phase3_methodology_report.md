# SupeRR Intelligence — Phase 3 Methodology Report: Clutch Performance & Reliability Index (CPRI)

## 1. Executive Summary & Architecture Overview
The Clutch Performance & Reliability Index (CPRI) is a composite statistical evaluation engine designed to quantify player performance under high-pressure conditions in Twenty20 cricket across the Indian Premier League (IPL) and Twenty20 Internationals (T20I).

CPRI integrates four dimensions:
1. **Pressure Impact (40%)**: Delivery-weighted expected run residuals, survival credit (for batters) / credited wickets (for bowlers), and contextual Win Probability Added (WPA) earned in pressure deliveries (Pressure Score >= 50.0).
2. **Pressure Adaptability (25%)**: Differential between a player's performance in high-pressure states versus low/moderate-pressure states, isolating players whose output elevates during crisis situations.
3. **Clutch Consistency (20%)**: Match-level reproducibility of positive clutch output across games, penalized for high cross-match variance.
4. **Reliability Confidence (15%)**: Empirical-Bayes reliability curve reflecting sample depth (N deliveries) to ensure rankings reflect stable skill rather than small-sample variance.

---

## 2. Mathematical Formulation

### 2.1 Pre-Delivery Dynamic Pressure Partitioning
From Phase 2A, each delivery has a pre-delivery pressure score P in [0, 100]. A delivery is classified as high-pressure if:
Pressure == True if P >= 50.0

### 2.2 Batter CPRI Formulation
For each batter i in competition scope s in {IPL, T20I}:
- **Pressure Run Residual Rate**:
  Rate_runs = (sum(actual_runs - expected_runs) / N_pressure) * 100
- **Pressure Dismissal Survival Rate**:
  Rate_dismissal = (sum(dismissal_outcome - expected_dismissal_prob) / N_pressure) * 100
- **Pressure WPA Rate**:
  Rate_wpa = (sum(batting_wpa) / N_pressure) * 100
- **Raw Pressure Impact**:
  Impact_raw = (Rate_runs - 12.0 * Rate_dismissal) + 25.0 * Rate_wpa
  (Where 12.0 runs represents the empirical T20 wicket replacement cost).
- **Adaptability**:
  Adaptability_raw = Impact_raw(pressure) - Impact_raw(non-pressure)
- **Consistency**:
  Consistency_raw = WinMatchRatio * 70.0 + max(0, 100.0 - sigma_match) * 0.30
- **Bayesian Shrinkage**:
  Metric_shrunk = (N * Metric_raw + M * mu_pop) / (N + M)
  (With prior weight M = 40.0 for impact/adaptability, and M = 5.0 for consistency).
- **Reliability Curve**:
  Score_reliability = 100 * (1 - exp(-N_total / 150.0))
- **Composite CPRI**:
  CPRI = 0.40 * S_impact + 0.25 * S_adapt + 0.20 * S_consist + 0.15 * S_rel

### 2.3 Bowler CPRI Formulation
For each bowler j in competition scope s:
- **Runs Prevented & Credited Wickets**:
  Rate_runs_saved = (sum(expected_runs - actual_runs) / N_pressure) * 100
  Rate_wickets = (sum(credited_wickets - expected_wicket_prob) / N_pressure) * 100
  Rate_bowler_wpa = (sum(bowling_wpa) / N_pressure) * 100
- **Raw Pressure Impact**:
  Impact_raw = (Rate_runs_saved + 12.0 * Rate_wickets) + 25.0 * Rate_bowler_wpa
- **Adaptability & Consistency**:
  Calculated analogously to batters, assessing the difference between high-pressure containment and standard baseline bowling.

---

## 3. Sample-Size Eligibility & Confidence Tiers
To ensure transparent reporting without arbitrarily hiding players:
- **High Confidence (Official Top 10 Eligibility)**: N_total >= 150 deliveries.
- **Moderate Confidence**: 60 <= N_total < 150 deliveries.
- **Low Confidence**: N_total < 60 deliveries.

All players across all confidence tiers are preserved in all_batter_rankings.csv and all_bowler_rankings.csv.
