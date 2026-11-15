# SupeRR Intelligence — Phase 2B: Expected Performance Intelligence Engine Validation Report

**Prepared by**: Senior Cricket Data Scientist & Machine Learning Researcher  
**Date**: November 12, 2026  
**Pipeline**: Phase 2B Expected Performance Intelligence Engine  
**Dataset Scope**: Indian Premier League (IPL) & Twenty20 International (T20I)  
**Deliverable Outputs**:
- \ml/phase2/expected_batting.py\
- \ml/phase2/expected_bowling.py\
- \ml/phase2/performance_delta.py\
- \ml/phase2/player_performance_aggregation.py\
- \ml/phase2/model_evaluation.py\
- \output/phase2/batter_delivery_expectations.csv\
- \output/phase2/bowler_delivery_expectations.csv\
- \output/phase2/batter_performance_summary.csv\
- \output/phase2/bowler_performance_summary.csv\
- \output/phase2/phase2b_model_evaluation.json\
- \output/phase2/phase2b_validation_report.md\
- \output/phase2/phase2b_assumptions.md\
- \	ests/test_expected_batting.py\
- \	ests/test_expected_bowling.py\
- \	ests/test_performance_delta.py\

---

## 1. Executive Summary

Phase 2B implements a state-of-the-art **Expected Performance Intelligence Engine** for **SupeRR Intelligence**. The engine establishes objective, player-agnostic expectations for every delivery bowled in IPL and T20I competitions and computes performance residuals (Actual minus Expected) under pressure.

### Key Milestones
1. **Four Specialized Machine Learning Models**:
   - Batter Expected Runs Model (Regressor)
   - Batter Dismissal Probability Model (Calibrated Classifier)
   - Bowler Expected Runs Conceded Model (Regressor)
   - Bowler Credited Wicket Probability Model (Calibrated Classifier)
2. **Chronological Match-Level Partitioning**: Split strictly across time into **569 Training Matches** (135,264 balls from 2022 to 2025), **122 Validation Matches**, and **122 Test Matches** (28,639 balls in 2026). Zero cross-match or future-match contamination exists.
3. **Transparent Residual Conventions**:
   - Positive batting residual indicates scoring above context par.
   - Positive bowling residual indicates conceding fewer runs than context par (sign reversed).
   - Wicket and run impacts are kept completely distinct and unbundled.
4. **Bayesian Shrinkage on Aggregates**: Player-level summaries apply empirical Bayes shrinkage (\(m=30\) prior balls) to prevent small-sample extreme outliers from distorting baselines, while explicitly categorizing players into **High**, **Moderate**, and **Low Confidence** sample tiers.
5. **100% Automated Test Pass Rate**: All 25 unit tests across the test suite passed cleanly.

---

## 2. Model Training & Evaluation Metrics

Evaluated on the held-out chronological test partition (28,639 unseen 2026 deliveries):

| Model Name | Target Variable | Primary Metric | Model Score | Baseline Score | Improvement | Calibration (Observed vs Predicted) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Batter Expected Runs** | \atter_runs\ | **RMSE** | **1.7990** | 1.8660 | **+3.59%** | Mean: 1.346 obs vs 1.348 pred |
| **Batter Dismissal Prob** | Striker Dismissal | **Log Loss** | **0.2007** | 0.2034 | **+1.33%** | Obs: **5.17%** vs Pred: **5.27%** |
| | | **Brier Score** | **0.04869** | 0.04901 | **+0.65%** | |
| **Bowler Expected Runs** | \owler_runs_conceded\ | **RMSE** | **1.7807** | 1.8626 | **+4.40%** | Mean: 1.395 obs vs 1.392 pred |
| **Bowler Wicket Prob** | \owler_wicket\ | **Log Loss** | **0.1970** | 0.1989 | **+0.96%** | Obs: **5.01%** vs Pred: **5.08%** |
| | | **Brier Score** | **0.04742** | 0.04763 | **+0.44%** | |

### Methodological Notes on Metric Interpretation
- **Why RMSE over MAE for Cricket Run Expectation**: In cricket delivery-level prediction, the target is discrete (\(0, 1, 2, 4, 6\)). Predicting the historical mode (\(1.0\)) mechanically yields an artificially low MAE (\(1.20\)), but fails completely as an expectation engine because it ignores boundaries and dots. The Gradient Boosting model optimizes the true expected value (\(E[Y|X]\)), achieving an RMSE reduction from \(1.866\) to \(1.799\) and yielding calibrated cumulative innings projections.

---

## 3. High vs Low Pressure Performance Dynamics

Analysis of out-of-sample delivery performance across pressure tiers demonstrates that the engine captures the behavioral shifts of elite T20 cricket:
- **Dismissal Risk Under Pressure**: In Low Pressure deliveries (\(\le 25\)), the expected striker dismissal probability is **4.65%**. In High Pressure deliveries (\(\ge 75\)), expected dismissal risk escalates to **7.59%** (\(+63.2\%\) increase in danger).
- **Death-Overs Scoring Velocity**: The expected scoring rate in the Death phase is **1.45 runs/ball** (8.70 RPO), compared to **1.18 runs/ball** (7.08 RPO) in the Powerplay.

---

## 4. Top Performing Players Under Contextual Expectations

*(Filtered to High Confidence sample tier \(\ge 150\) balls; Bayesian shrunk)*

### Top Batters by Shrunk Run Residual (Runs Added vs Context Expectation)
- **IPL**:
  1. **Abhishek Sharma**: \(+183.1\) raw residual, **\(+175.6\)** shrunk residual (\(+17.4\) runs/100 balls above context par)
  2. **Vaibhav Sooryavanshi**: \(+149.2\) raw residual, **\(+139.8\)** shrunk residual (\(+23.2\) runs/100 balls above context par)
  3. **Suryakumar Yadav**: \(+144.5\) raw residual, **\(+140.2\)** shrunk residual (\(+15.1\) runs/100 balls above context par)
  4. **Phil Salt**: \(+124.6\) raw residual, **\(+118.5\)** shrunk residual (\(+18.8\) runs/100 balls above context par)
- **T20I**:
  1. **Abhishek Sharma**: \(+172.4\) raw residual, **\(+162.1\)** shrunk residual (\(+28.2\) runs/100 balls above context par)
  2. **Suryakumar Yadav**: \(+168.1\) raw residual, **\(+163.7\)** shrunk residual (\(+16.8\) runs/100 balls above context par)
  3. **Jos Buttler**: \(+155.2\) raw residual, **\(+148.8\)** shrunk residual (\(+18.2\) runs/100 balls above context par)
  4. **Tim David**: \(+139.5\) raw residual, **\(+131.6\)** shrunk residual (\(+22.1\) runs/100 balls above context par)

### Top Bowlers by Shrunk Run Residual (Runs Saved vs Context Expectation)
- **IPL**:
  1. **Jasprit Bumrah**: \(+168.4\) raw residual, **\(+164.2\)** shrunk residual (\(-13.8\) runs conceded/100 balls vs context par, 58 wickets)
  2. **Sunil Narine**: \(+152.1\) raw residual, **\(+148.9\)** shrunk residual (\(-12.1\) runs conceded/100 balls vs context par, 53 wickets)
  3. **Matheesha Pathirana**: \(+134.8\) raw residual, **\(+129.5\)** shrunk residual (\(-15.4\) runs conceded/100 balls vs context par, 46 wickets)
  4. **Bhuvneshwar Kumar**: \(+121.2\) raw residual, **\(+118.1\)** shrunk residual (\(-9.8\) runs conceded/100 balls vs context par, 49 wickets)
- **T20I**:
  1. **Rashid Khan**: \(+176.2\) raw residual, **\(+171.9\)** shrunk residual (\(-14.2\) runs conceded/100 balls vs context par, 64 wickets)
  2. **Mustafizur Rahman**: \(+149.8\) raw residual, **\(+145.2\)** shrunk residual (\(-13.1\) runs conceded/100 balls vs context par, 56 wickets)
  3. **Maheesh Theekshana**: \(+142.1\) raw residual, **\(+138.4\)** shrunk residual (\(-11.9\) runs conceded/100 balls vs context par, 48 wickets)

---

## 5. Automated Unit Test Results

Executed via: \python -m unittest discover -s tests -p \"test_*.py\" -v\

`	ext
Ran 25 tests in 9.645s

OK
`

- **Tests Passed**: **25 / 25** (10 from 	est_pressure_engine.py, 5 from 	est_expected_batting.py, 5 from 	est_expected_bowling.py, 5 from 	est_performance_delta.py).
- **Tests Failed**: **0**.

---

## 6. Documented Limitations & Phase 2C Readiness

1. **Venue Effect**: While enue_id exists in raw metadata, 35 venues have fewer than 3 matches. Venue-specific pitch indices are deferred to Phase 2C to avoid overfitting sparse venues.
2. **Distinct Run & Wicket Aggregation**: Runs saved and wickets taken are purposefully unbundled in the summary tables. Synthesizing them into a singular contextual index (CPRI) is reserved for Phase 2C.

> **VERDICT: PHASE 2B IS OFFICIALLY VALIDATED AND READY FOR PHASE 2C.**
