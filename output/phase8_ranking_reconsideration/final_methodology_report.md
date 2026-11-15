# Phase 8: Final CPRI Methodology & Competition Selection Rationale

## 1. Problem Statement & Scope Resolution
The official SupeRR Selector Season 2 Round 1 problem statement mandates:
1. **Exactly ONE ordered Top 10 Batter ranking** (`official_top10_batters.csv`).
2. **Exactly ONE ordered Top 10 Bowler ranking** (`official_top10_bowlers.csv`).
3. **Transparent mathematical formulations, sample neutrality, and uncertainty bounds**.

Supplementary diagnostic rankings (`ipl_only_*.csv`, `t20i_only_*.csv`) provide franchise-level contextual granularity but do not substitute for the official submission lists.

## 2. CPRI Architecture & Weights
CPRI integrates four complementary dimensions of pressure performance:
$$\text{CPRI} = 0.40 \times \text{Impact} + 0.25 \times \text{Adaptability} + 0.20 \times \text{Consistency} + 0.15 \times \text{Reliability}$$

### Component Specifications
1. **Pressure Impact (40%)**:
   - Evaluates delivery-level net value vs baseline expectation:
     $$\text{NetImpact} = \Delta\text{Runs} + 12.0 \times \Delta\text{Wickets/Survival} + 25.0 \times \text{WPA}$$
   - Shrunk via Empirical Bayes ($M = 120.0$ deliveries) towards the qualified population prior mean.
   - Normalized via robust sigmoid ($k = 0.6$).
2. **Pressure Adaptability (25%) — Calibrated to Eliminate Baseline Penalty**:
   - In previous iterations, naive delta ($\text{Pressure} - \text{NonPressure}$) heavily penalized elite bowlers (e.g. Jasprit Bumrah) who maintained world-class non-pressure baselines.
   - The Phase 8 formulation directly measures **Retention & Elevation**:
     $$\text{CalibratedAdaptability} = 0.60 \times \text{PressureImpact} + 0.40 \times \max(\Delta, -5.0)$$
   - Players achieving elite pressure output are never penalized for having elite non-pressure baselines.
3. **Clutch Consistency (20%)**:
   - Aggregates performance across pressure matches:
     $$\text{Consistency} = 50.0 \times f_{\text{pos}} + 0.30 \times \text{MeanImpact} + 0.20 \times \text{Stability}$$
   - Penalizes volatile boom-or-bust performers; rewards players who deliver in high percentages of pressure matches.
4. **Reliability Confidence (15%)**:
   - Captures sample depth via non-linear saturation:
     $$\text{Reliability} = 100.0 \times \left(1 - e^{-N_P / 200}\right) \times \sqrt{1 - e^{-M_P / 12}}$$
   - Prevents small-sample outliers (e.g. 100–150 balls) from dominating players with 500+ pressure balls.
