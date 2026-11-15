# Phase 2B: Expected Performance Intelligence Engine — Assumptions & Domain Principles

This document records the mathematical formulations, cricket domain principles, and machine learning assumptions adopted in Phase 2B of **SupeRR Intelligence**.

---

## 1. Context-Based Neutral Expectations

1. **Player-Agnostic Context Baseline**:
   - The primary purpose of Phase 2B is to establish an objective baseline of what an **average replacement-level league player** would produce given the exact pre-delivery match context.
   - Striker identity and bowler identity are deliberately excluded from model training features to prevent circular reasoning. Player quality is then isolated as the **residual (Actual minus Expected)**.

2. **Pre-Delivery Integrity (Zero Future Leakage)**:
   - All input features for batting and bowling models (pressure_score, score_before, wickets_lost_before, alls_remaining, wickets_in_hand, crr_clean, rr_clean, uns_req_clean, innings_phase, competition_scope) represent information available **before** the bowler begins their run-up.
   - Final match scores, total innings runs, current delivery runs, and future events are strictly forbidden as model inputs.

---

## 2. Model Architecture & Evaluation Rationales

### 2.1 Batter Models
- **Expected Batter Runs**: Trained using HistGradientBoostingRegressor with L2 regularization to predict runs off the bat on each delivery (0, 1, 2, 3, 4, 6).
  - Out-of-Sample RMSE: **1.7990** (outperforming constant baseline of 1.8660).
  - *Note on MAE*: In cricket delivery-level scoring, modal outcomes are 0 or 1. A regression model outputs expected values (e.g., 1.35), which mathematically inflates MAE compared to predicting the mode 1.0, but achieves strictly superior RMSE and calibrated expected sums.
- **Dismissal Probability Model**: Trained using HistGradientBoostingClassifier to estimate probability of striker dismissal on the delivery.
  - Test Log Loss: **0.2007** (outperforming baseline 0.2034).
  - Test Brier Score: **0.04869** (outperforming baseline 0.04901).
  - Observed test dismissal rate: **5.17%**; Predicted mean dismissal rate: **5.27%** (superb calibration).

### 2.2 Bowler Models
- **Expected Bowler Runs Conceded**: Evaluates expected runs conceded, incorporating batter runs, wides, and no-ball penalties, while strictly excluding byes and leg-byes according to MCC Law.
  - Test RMSE: **1.7807** (outperforming baseline 1.8626).
- **Bowler Wicket Probability Model**: Evaluates legal credited wicket probability (Bowled, Caught, LBW, Stumped, Hit Wicket).
  - Test Log Loss: **0.1970** (outperforming baseline 0.1989).
  - Test Brier Score: **0.04742** (outperforming baseline 0.04763).
  - Observed test wicket rate: **5.01%**; Predicted mean wicket rate: **5.08%** (superb calibration).

---

## 3. Residual Definitions & Sign Conventions

### Batting Conventions
1. **Batting Run Residual**:
   \[
   \Delta_{\text{run}} = \text{Actual Batter Runs} - \text{Expected Batter Runs}
   \]
   - Positive indicates better-than-expected batting scoring.
2. **Batting Dismissal Residual**:
   \[
   \Delta_{\text{dismissal}} = \text{Expected Dismissal Prob} - \text{Actual Dismissal (0 or 1)}
   \]
   - Surviving a high-risk delivery (0.20 risk, 0 dismissal) grants \(+0.20\).
   - Getting out grants \(\text{Prob} - 1.0\) (negative impact).
3. **Pressure Leverage Multiplier**:
   \[
   M_{\text{pressure}} = 1.0 + \frac{\text{Pressure Score}}{100.0}
   \]
   - Scales from 1.0 at zero pressure to 2.0 at maximum 100 pressure.
   \[
   \Delta_{\text{pressure\_run}} = \Delta_{\text{run}} \cdot M_{\text{pressure}}
   \]

### Bowling Conventions
1. **Bowling Run Residual (Reversed Sign)**:
   \[
   \Delta_{\text{bowl\_run}} = \text{Expected Runs Conceded} - \text{Actual Runs Conceded}
   \]
   - Positive indicates better-than-expected bowling (conceding fewer runs than context par).
2. **Bowling Wicket Residual**:
   \[
   \Delta_{\text{bowl\_wicket}} = \text{Actual Credited Wicket (0 or 1)} - \text{Expected Wicket Prob}
   \]
   - Taking a wicket grants \(1.0 - \text{Prob}\) (positive impact).
3. **Pressure Leverage Multiplier**:
   \[
   \Delta_{\text{pressure\_bowl\_run}} = \Delta_{\text{bowl\_run}} \cdot M_{\text{pressure}}
   \]

---

## 4. Empirical Bayes Shrinkage & Small-Sample Reporting

- **Prior Neutral Mean**: Standardized context expectation has a mean residual of 0.0.
- **Shrinkage Formulation**:
  \[
  \text{Shrunk Residual Per Ball} = \left(\frac{N}{N + m}\right) \cdot \left(\frac{\text{Raw Residual}}{N}\right)
  \]
  where \(m = 30\) pseudo-balls.
- **Sample Reliability Tiers**:
  - **High Confidence**: \(N \ge 150\) deliveries.
  - **Moderate Confidence**: \(60 \le N < 150\) deliveries.
  - **Low Confidence (Small Sample)**: \(N < 60\) deliveries.
  - Small sample players are **never hidden or dropped**; their unadjusted and shrunk metrics are reported transparently alongside their confidence tier.
