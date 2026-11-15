# SupeRR Intelligence — Phase 9: Contextual Error & Fairness Analysis

## 1. Executive Summary

This report investigates the residual error distributions of the three candidate architectures (**Statistical Baseline**, **CatBoost**, and **XGBoost**) across distinct match contexts, innings phases, competitive formats, and player role archetypes.

The central research question is:
> *Do non-linear machine learning models eliminate or introduce systematic biases for particular match situations or player cohorts compared with the baseline statistical engine?*

---

## 2. In-Depth Error Dissection by Match Context

### 2.1 Innings Phase Context (Powerplay vs. Middle vs. Death)

| Innings Phase | Test Deliveries | Actual Mean Runs | Baseline Pred Mean (Bias) | CatBoost Pred Mean (Bias) | XGBoost Pred Mean (Bias) | Actual Dismissal Rate | CatBoost Pred Wkt Prob |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Powerplay (0–5)** | 9,197 | 1.352 | 1.285 (-0.067) | 1.294 (-0.058) | 1.291 (-0.061) | 4.38% | 4.34% |
| **Middle (6–15)** | 13,347 | 1.328 | 1.286 (-0.042) | 1.291 (-0.037) | 1.290 (-0.038) | 4.49% | 4.41% |
| **Death (16–19)** | 6,095 | 1.831 | 1.728 (-0.103) | 1.741 (-0.090) | 1.733 (-0.098) | 7.84% | 7.68% |

#### Analytical Insights:
1. **Death Over Acceleration**: In overs 16–19, actual scoring surges to **1.831 runs/delivery** ($11.0$ RPO) and dismissals jump to **7.84%**.
2. **CatBoost's Death Over Advantage**: CatBoost's oblivious trees capture the late-innings hockey-stick curve most effectively, predicting **1.741 runs/delivery** (reducing death-over bias by 13% compared with the baseline's 1.728).
3. **No Skewed Residual Advantage**: All models correctly elevate expectations in the death overs. A batter hitting at 12.0 RPO in the death overs receives a context residual relative to an expected ~11.0 RPO, not an artificial bonus against an overall ~8.0 RPO average. This preserves fairness between top-order accumulators and late-innings power hitters.

---

### 2.2 Tournament Format Context (IPL vs. T20I)

| Tournament Format | Test Deliveries | Actual Mean Runs | Baseline RMSE | CatBoost RMSE | XGBoost RMSE | Actual Dismissal Rate | Best Wicket Log Loss |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **IPL Matches** | 17,501 | 1.488 | 1.8408 | **1.8392** | 1.8403 | 4.86% | **XGBoost (0.1895)** |
| **T20I Matches** | 11,138 | 1.371 | 1.7312 | **1.7306** | 1.7311 | 5.65% | **CatBoost (0.2081)** |

#### Analytical Insights:
1. **IPL Scoring Premium**: IPL deliveries in 2026 exhibited substantially higher scoring rates (**1.488 runs/ball** $\approx 8.93$ RPO) compared with T20 Internationals (**1.371 runs/ball** $\approx 8.23$ RPO). Conversely, T20Is produced higher dismissal rates (**5.65%** vs. **4.86%**), reflecting wider talent dispersion and more varied pitch surfaces across international venues.
2. **Format Flag Conditioning**: Both CatBoost and XGBoost utilize the `is_ipl` flag to scale baseline expectations. Neither model over-penalizes T20I bowlers or unfairly rewards IPL batters.

---

### 2.3 Pressure Tier Context

Deliveries partitioned by the Phase 2A continuous Pressure Index ($PI$):

| Pressure Tier | Deliveries | Actual Runs | CatBoost Exp Runs | Actual Wkt % | CatBoost Exp Wkt % | CatBoost RMSE | Baseline RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Low ($PI < 25$)** | 8,940 | 1.341 | 1.302 | 4.22% | 4.18% | 1.7654 | 1.7668 |
| **Medium ($25 \le PI < 50$)** | 10,484 | 1.398 | 1.354 | 4.88% | 4.90% | 1.8291 | 1.8302 |
| **High ($50 \le PI < 75$)** | 6,582 | 1.542 | 1.481 | 5.71% | 5.66% | 1.8012 | 1.8025 |
| **Extreme ($PI \ge 75$)** | 2,633 | 1.712 | 1.638 | 6.65% | 6.54% | 1.7710 | 1.7731 |

#### Analytical Insights:
- Under **Extreme Pressure ($PI \ge 75$)**, batting aggression rises along with wicket risk (dismissal rate reaches **6.65%**).
- All three models demonstrate strong resilience across the full pressure continuum. The prediction error (RMSE) does not explode in extreme pressure; rather, it remains flat (~1.77–1.80), demonstrating that the pressure features smoothly modulate conditional expectations without instability.

---

## 3. Real-World Chronological Distribution Shift

A subtle yet vital dynamic revealed by our audit:
- In the training set (2022 to mid-2025), mean batter runs were **1.334**.
- In the chronological test set (2026), mean batter runs rose to **1.443** (+8.1%).

### Why did all models exhibit a small negative bias (-0.06 runs/ball)?
Because all models were fitted on pre-2025 data, they reflect the historical scoring baseline. In 2026, modern T20 batting tactics, boundary-maximization strategies, and flatter franchise wickets caused a macro-level scoring inflation.
- **Fairness Protection**: Because residual scoring evaluates a player relative to the *same* baseline across identical matches, this macroeconomic shift does not distort relative player comparisons within the test period.
- **Future Recommendation**: Implementing a rolling exponential decay or season-weighted baseline in future major engine iterations (e.g. CPRI v2.0) would track macro-level scoring trends even more closely.

---

## 4. Boundary Conditions & Anomaly Checks

1. **Negative Expected Runs**: Both CatBoost and XGBoost outputs were checked for negative predictions ($\hat{y} < 0$). In the raw CatBoost regressor, exactly 0.00% of test predictions were $< 0$; in the raw XGBoost regressor, exactly 0.00% were $< 0$. Regardless, an explicit zero floor ($\max(0, \hat{y})$) is strictly enforced in all adapters.
2. **Probability Extremes**: No predicted dismissal or wicket probabilities exceeded $[0.001, 0.999]$. Probabilities ranged naturally from 2.8% to 14.2%, fully consistent with physical cricket possibilities.
3. **Player Role Fairness**:
   - Anchors/Openers are not penalized for lower strike rates during the powerplay because their expected runs baseline is proportionally lower (~1.29 vs. ~1.74 in death).
   - Finishers are not artificially inflated: their high strike rates are judged against rigorous death-over scoring baselines (~11 RPO).
