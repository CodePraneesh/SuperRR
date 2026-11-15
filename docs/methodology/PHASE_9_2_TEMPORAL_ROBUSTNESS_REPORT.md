# SupeRR Intelligence — Phase 9.2: Temporal Robustness & Final Model Decision

## 1. Executive Summary

This report resolves the remaining empirical and statistical questions identified in the Phase 9.1 evaluation:
1. **Root Cause of Temporal Drift**: The scoring rate rise from **1.334 runs/ball** (2022–2025) to **1.443 runs/ball** (2026) is driven by two measurable real-world factors: (a) genuine tactical evolution in modern T20 cricket (boundary percentage rose from 16.56% to 20.14%), and (b) dataset composition shift (IPL matches, which score at ~1.49 runs/ball, constituted 53.2% of 2026 deliveries vs. 41.6% in 2024).
2. **Chronological Split Boundary Sensitivity**: Exactly 3 matches took place on February 1, 2026. A sensitivity re-evaluation enforcing a strict date boundary ($\ge$ 2026-02-02 vs. $\ge$ 2026-02-01) proves that the performance differential between CatBoost and the Baseline remains identical ($\Delta \text{RMSE} = +0.00130$ vs. $+0.00128$).
3. **Formal Hypothesis Testing & Effect Sizes**: A paired match-level hypothesis test ($N = 122$ matches) confirms that CatBoost's expected runs RMSE reduction is statistically significant ($p = 0.00297$, paired $t = 3.03$), but the effect size is small (Cohen's $d = 0.2745$, relative reduction = $0.071\%$). For dismissal/wicket probability, the difference is statistically indistinguishable ($p = 0.513$, Cohen's $d = 0.059$).
4. **Final Model Decision**: **Retain the Statistical Baseline (`HistGradientBoosting`) for Production CPRI v1.0.** The marginal $0.07\%$ accuracy gain does not justify adding heavy external C++ binaries to a frozen production engine. CatBoost is designated as the primary candidate for future CPRI v2.0 development.

---

## 2. Temporal Drift Investigation

### 2.1 Macro Scoring Shift (2022 to 2026)

| Year | Active Matches | Deliveries | Batter Runs / Ball | Bowler Runs Conceded / Ball | Dot Ball % | Boundary % (4s & 6s) | Striker Dismissal % | IPL Delivery Share % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2022** | 177 | 42,261 | 1.2722 | 1.3203 | 40.46% | 16.56% | 5.08% | 42.38% |
| **2023** | 137 | 32,686 | 1.3371 | 1.3822 | 38.76% | 17.81% | 5.18% | 54.29% |
| **2024** | 174 | 41,114 | 1.3474 | 1.3974 | 39.76% | 18.23% | 5.43% | 41.60% |
| **2025** | 184 | 43,291 | 1.3519 | 1.4002 | 39.66% | 18.13% | 5.41% | 39.17% |
| **2026** | 141 | 32,883 | **1.4411** | **1.4930** | **37.99%** | **20.14%** | 5.24% | **53.22%** |

### 2.2 Format-Specific Evolution

| Year | IPL Deliveries | IPL Mean Batter Runs | IPL Boundary % | T20I Deliveries | T20I Mean Batter Runs | T20I Boundary % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2022** | 17,909 | 1.2870 | 17.21% | 24,352 | 1.2614 | 16.08% |
| **2023** | 17,745 | 1.3699 | 18.53% | 14,941 | 1.2982 | 16.96% |
| **2024** | 17,103 | 1.4417 | 20.09% | 24,011 | 1.2803 | 16.90% |
| **2025** | 16,959 | 1.4644 | 20.63% | 26,332 | 1.2794 | 16.52% |
| **2026** | 17,501 | **1.4928** | **21.46%** | 15,382 | **1.3823** | **18.65%** |

### Analytical Findings on Drift:
1. **T20 Boundary Inflation**: Across both domestic franchise cricket and international cricket, teams adopted significantly more aggressive powerplay hitting and death-over bat speeds. Boundaries rose from **1 in 6.0 balls** in 2022 to **1 in 4.9 balls** in 2026.
2. **Dataset Composition**: IPL deliveries made up **53.2%** of the 2026 sample versus ~40% in 2024–2025. Because IPL matches feature higher scoring surfaces (1.493 runs/ball) than T20 Internationals (1.382 runs/ball), this composition shift mechanically increased aggregate 2026 scoring.
3. **Model Calibration Impact**: All models trained on 2022–2025 data under-predicted 2026 scoring by ~0.06 runs/ball on average. However, because CPRI evaluates players relative to the *same* baseline within that test period, player ranking order is completely unaffected.

---

## 3. Chronological Split Boundary Sensitivity

### 3.1 Audit of February 1, 2026 Matches
Three matches took place on February 1, 2026:
- **Match 41851** (South Africa vs. West Indies, comp 3090) $\rightarrow$ Assigned to **Validation**
- **Match 48917** (Pakistan vs. Australia, comp 3354) $\rightarrow$ Assigned to **Validation**
- **Match 48611** (Sri Lanka vs. England, comp 3345) $\rightarrow$ Assigned to **Held-Out Test**

Because match splitting sliced strictly at the 85th percentile match index (Match Index 691 of 813), same-day matches were split across partitions. Only 1 bilateral series (England in Sri Lanka) crossed partitions (Match 1 in Val, Matches 2 & 3 in Test). However, no series-level features or target leaks were present.

### 3.2 Sensitivity Re-Evaluation Across Strict Date Boundaries

| Split Definition | Test Matches | Test Deliveries | Baseline Bat Runs RMSE | CatBoost Bat Runs RMSE | $\Delta \text{RMSE}$ (Gain) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Original Partition (Index 691)** | 122 | 28,639 | 1.799005 | 1.797720 | **+0.001284** |
| **Strict Date ($\ge \text{2026-02-02}$)** | 121 | 28,406 | 1.799331 | 1.798030 | **+0.001301** |
| **Strict Date ($\ge \text{2026-02-01}$)** | 124 | 28,987 | 1.799139 | 1.797864 | **+0.001275** |

**Conclusion**: The performance differential between CatBoost and the Baseline is invariant to whether the boundary is placed at Index 691, February 2, or February 1.

---

## 4. Formal Hypothesis Testing & Effect Size Analysis

### 4.1 Frequentist vs. Bootstrap $P(\Delta > 0)$
In the Phase 9.1 report, $P(\Delta > 0) = 1.0$ from the bootstrap distribution was reported as an informal indicator. In formal statistical theory:
- An empirical bootstrap coverage probability $P(\Delta^* > 0)$ reflects the posterior mass under a flat prior, **not** a formal null-hypothesis significance test ($H_0: \mu_\Delta = 0$).
- To rigorously test $H_0$, a **paired match-level hypothesis test** ($N = 122$ matches) was performed, evaluating the distribution of match-level performance differences:
  $$\Delta_m = \text{RMSE}_{\text{Baseline}, m} - \text{RMSE}_{\text{CatBoost}, m}$$

### Table 1: Paired Match-Level Hypothesis Test Results ($N = 122$ Matches)

| Target Metric | Mean Match Difference ($\bar{\Delta}$) | SD Across Matches | Standard Error ($\text{SE}$) | Paired $t$-statistic | Two-Tailed $p$-value | Cohen's $d$ Effect Size | Statistically Significant? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Batter Runs RMSE** | **+0.001209** | 0.004402 | 0.000399 | **+3.0322** | **$p = 0.00297$** | **0.2745** (Small) | **YES ($p < 0.003$)** |
| **Bowler Runs RMSE** | **+0.001222** | 0.004170 | 0.000377 | **+3.2357** | **$p = 0.00157$** | **0.2929** (Small) | **YES ($p < 0.002$)** |
| **Batter Dismissal LogLoss** | +0.000035 | 0.001713 | 0.000155 | +0.2249 | $p = 0.8224$ | 0.0204 (Negligible) | **NO ($p > 0.80$)** |
| **Bowler Wicket LogLoss** | +0.000085 | 0.001426 | 0.000129 | +0.6561 | $p = 0.5130$ | 0.0594 (Negligible) | **NO ($p > 0.50$)** |

### Interpretation:
1. **Statistical Significance vs. Practical Significance**:
   - For expected runs, CatBoost's improvement is **statistically significant ($p = 0.00297$)**.
   - However, the effect size is small (**Cohen's $d = 0.2745$**), representing a relative reduction of just **$0.071\%$** ($0.0012$ runs/ball).
2. **Wicket Predictions**:
   - For binary wicket prediction, there is **zero statistically significant difference** between CatBoost and `HistGradientBoosting` ($p = 0.513$).

---

## 5. Comprehensive Multi-Dimensional Comparison

| Dimension | Statistical Baseline (`HistGradientBoosting`) | CatBoost | XGBoost |
| :--- | :--- | :--- | :--- |
| **Runs Prediction (RMSE)** | 1.7990 | **1.7977** (+0.07% gain, $p < 0.003$) | 1.7986 |
| **Wicket Prediction (Log Loss)** | 0.1970 | 0.1969 (no sig. difference) | **0.1968** |
| **Calibration (Brier Reliability)** | $3.07 \times 10^{-6}$ | $2.95 \times 10^{-5}$ | **$1.45 \times 10^{-6}$** |
| **Ranking Agreement with Baseline** | 1.0000 (Identity) | **0.9943** (Batting) / **0.9954** (Bowling) | **0.9961** (Batting) / **0.9982** (Bowling) |
| **Top 10 Player Overlap** | 10/10 | **9/10 to 10/10** | **10/10** |
| **External Dependencies** | **None** (Built into `scikit-learn`) | Requires `catboost` C++ binaries (~100 MB) | Requires `xgboost` C++ binaries |
| **Serverless / Docker Portability** | **Frictionless** (Standard Python wheel) | Occasional compilation / wheel issues on ARM/Alpine | Standard wheel support |
| **Training Duration** | 8.32 seconds | 15.81 seconds | **7.05 seconds** |

---

## 6. Final Model Decision

### Recommendation for CPRI v1.0 (Production)
**Retain the Statistical Baseline (`HistGradientBoosting`).**
- **Justification**:
  1. The practical effect size of CatBoost's improvement on delivery-level runs is tiny ($d = 0.27$, relative gain = $0.07\%$).
  2. For wicket probabilities, there is no statistically detectable improvement ($p > 0.50$).
  3. Player pressure rankings are virtually identical ($r > 0.994$, 90–100% Top 10 overlap).
  4. Retaining `scikit-learn`'s native implementation preserves operational simplicity, rapid container builds, and zero external C++ binary dependencies for Render and local deployments.

### Recommendation for CPRI v2.0 (Future Major Release)
**Adopt CatBoost for CPRI v2.0 as part of an engine overhaul.**
- When CPRI v1.0's production freeze is officially lifted in a future development cycle, CatBoost should be deployed alongside:
  1. A dynamic rolling 12-month format baseline to address temporal drift.
  2. CatBoost's validated symmetric oblivious tree architecture, which excels at late-innings hockey-stick acceleration.
  3. Pre-trained and verified CatBoost model artifacts archived in `output/phase9_ml_evaluation/models/`.

---

## 7. Status of Production Artifacts
- **`CPRI-v1.0.0-PROD-FREEZE`**: Intact and preserved.
- **Phase 8 Official Top 10 Rankings**: Intact and preserved (`official_top10_batters.csv`, `official_top10_bowlers.csv`).
- **Phase 9 Test Suites**: **211/211 automated unit tests passing**.
