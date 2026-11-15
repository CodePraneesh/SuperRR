# SupeRR Intelligence — Phase 9: Dataset and Feature Audit

## 1. Executive Summary

This document establishes the formal data foundation, chronological match partitioning, target variable definitions, and feature verification for the Phase 9 Context-Aware Machine Learning Model Comparison.

All experiments strictly adhere to the project constraints:
- **No modification to frozen Phase 1–3.5 or Phase 8 ranking pipelines.**
- **Strictly zero post-delivery data leakage.**
- **Grouped, chronological match validation** ensuring zero cross-contamination between training and evaluation deliveries.
- **Strict adherence to cricket laws** regarding batter vs. non-striker dismissals and credited bowler wickets.

---

## 2. Source Data Inventory & Cryptographic Fingerprints

| File Description | Relative Path | Rows / Matches | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| **Pressure Scored Deliveries** | `output/phase2/pressure_scored_deliveries.csv` | 200,999 rows (121 cols) | `fd499a1285f41e7c190cbe0375f97368664f69edc17d6e3beed36677034e5952` |
| **Enriched Matches** | `output/processed/matches_enriched.csv` | 883 matches | `b14234814fb52bbcea65b788646a7a4a082cd7f3a84696456599b539ee938356` |

### Scope Filtering Criteria
1. **Competition Scope**: Filtered by `in_scope_competition == True` (IPL 2022–2025 and T20 Internationals 2022–2026).
2. **Abandoned Matches Excluded**: Exactly 40 abandoned or "No result" matches removed to eliminate artificial or unrepresentative run-rate distortions.
3. **Innings Scope**: Standard innings 1 and 2 only (super overs excluded from regular regression training).
4. **Final Modeling Dataset**: **192,235 deliveries** across **813 active matches**.

---

## 3. Chronological Match-Grouped Partitioning

Deliveries from the same cricket match are inherently correlated (shared pitch conditions, stadium dimensions, match weather, tactical momentum). Random delivery-level K-fold cross-validation introduces severe data leakage and artificially deflates out-of-sample error estimates.

To guarantee zero leakage, the dataset is partitioned **chronologically by match date** at the match level:

```
Match Timeline: 2022-01-22  =============================================>  2026-11-01
[------------------ Train (70%) ------------------][--- Val (15%) ---][--- Test (15%) ---]
 569 Matches (135,264 balls)                         122 Matches         122 Matches
 2022-01-22 to 2025-05-26                            28,332 balls        28,639 balls
```

### Partition Summary Table

| Split | Match Count | Delivery Count | Date Range | Primary Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **Train** | **569** | **135,264** | 2022-01-22 to 2025-05-26 | Feature scaling, tree learning, base estimator fitting |
| **Validation** | **122** | **28,332** | 2025-05-27 to 2026-02-01 | Early stopping (CatBoost / XGBoost), hyperparameter tuning |
| **Held-Out Test** | **122** | **28,639** | 2026-02-01 to 2026-11-01 | Final out-of-sample benchmarking, calibration, subgroup analysis |

### Mathematical Proof of Non-Leakage
- $\text{Train Matches} \cap \text{Val Matches} = \emptyset$ (verified: 0 overlaps)
- $\text{Train Matches} \cap \text{Test Matches} = \emptyset$ (verified: 0 overlaps)
- $\text{Val Matches} \cap \text{Test Matches} = \emptyset$ (verified: 0 overlaps)

---

## 4. Target Variables & Cricket Rules Verification

Every delivery target is strictly defined in compliance with official cricket scoring and MCC Laws:

### 1. Batting: Expected Batter Runs (`batter_runs`)
- **Definition**: Runs scored directly off the bat by the striker.
- **Range**: Discrete integers 0, 1, 2, 3, 4, 5, 6.
- **Exclusions**: Wides, no-ball penalties, byes, leg-byes, and penalty runs are strictly excluded.
- **Statistical Behavior**: Zero-inflated (~44.2% of all balls are dots in the training sample).

### 2. Batting: Striker Dismissal Probability (`striker_dismissed`)
- **Definition**: Indicator that the **striker** was dismissed on this specific delivery (`(dismissed_player_id == striker_id) & (is_wicket == 1)`).
- **Critical Cricket Integrity Rule**: When a non-striker is run out (e.g. attempting an impossible single or backing up too far), `striker_dismissed = 0`. The striker's wicket was not surrendered, and attributing non-striker run outs to striker dismissal expectation violates player evaluation fairness.
- **Training Frequency**: 5.2305%
- **Test Frequency**: 5.1678%

### 3. Bowling: Expected Runs Conceded (`bowler_runs_conceded`)
- **Definition**: Runs legally charged to the bowler's personal figures: `batter_runs + extras_wides + extras_noballs`.
- **Exclusions**: Byes, leg-byes, and penalty runs (MCC Laws 21, 22, 23).
- **Training Mean**: 1.3827 runs/ball
- **Test Mean**: 1.4961 runs/ball

### 4. Bowling: Credited Bowler Wicket Probability (`bowler_wicket`)
- **Definition**: Binary flag identifying dismissals credited to the bowler: `Bowled`, `Caught`, `LBW`, `Stumped`, and `Hit Wicket`.
- **Exclusions**: Strictly excludes `Run Out`, `Retired Out`, `Obstructing the Field`, and `Timed Out`.
- **Training Frequency**: 5.0605%
- **Test Frequency**: 5.0141%

---

## 5. Feature Audit & Pre-Delivery Information Integrity

All features are strictly constrained to information observable **prior to the bowler commencing their run-up**.

### Core Feature Set (13 Features — Parity Set)
Used by Baseline HistGradientBoosting, CatBoost Core, and XGBoost Core for exact architectural comparison:

| Feature Name | Type | Description | Train Min | Train Mean | Train Max | Nulls |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `pressure_score` | float | Phase 2A continuous Pressure Index (0–100) | 0.00 | 38.64 | 100.00 | 0 |
| `score_before` | int | Cumulative team score before delivery | 0 | 79.42 | 287 | 0 |
| `wickets_lost_before` | int | Wickets lost before delivery | 0 | 2.84 | 9 | 0 |
| `balls_remaining` | int | Balls remaining in innings (120 - legal_balls_before) | 0 | 60.36 | 120 | 0 |
| `wickets_in_hand` | int | Wickets remaining before delivery (10 - wickets_lost) | 1 | 7.16 | 10 | 0 |
| `crr_clean` | float | Current Run Rate before delivery (clipped [0, 36]) | 0.00 | 8.01 | 36.00 | 0 |
| `is_powerplay` | int | Overs 0–5 indicator flag | 0 | 0.30 | 1 | 0 |
| `is_middle` | int | Overs 6–15 indicator flag | 0 | 0.49 | 1 | 0 |
| `is_death` | int | Overs 16–19 indicator flag | 0 | 0.21 | 1 | 0 |
| `innings` | int | Innings number (1 or 2) | 1 | 1.48 | 2 | 0 |
| `is_ipl` | int | Tournament format flag (1 = IPL, 0 = T20I) | 0 | 0.58 | 1 | 0 |
| `rrr_clean` | float | Required Run Rate for chase (0.0 in 1st inn) | 0.00 | 4.38 | 36.00 | 0 |
| `runs_req_clean` | float | Runs required for chase (0.0 in 1st inn) | 0.00 | 45.12 | 288.00 | 0 |

### Extended Context Feature Set (17 Features)
Evaluated in CatBoost and XGBoost to assess if additional pre-delivery match context provides non-linear predictive gains:
- `target_clean`: First innings score + 1 (clipped $\ge 0$).
- `balls_remaining_ratio`: `balls_remaining / 120.0` (continuous normalized [0, 1]).
- `wickets_ratio`: `wickets_in_hand / 10.0` (continuous normalized [0.1, 1.0]).
- `format_par_score`: Baseline format par total (160.0 for T20I, 175.0 for IPL).

### Documentation of Unobservable / Omitted Variables
The original data pack does not record:
1. **Ball-by-ball pitch deterioration metrics** (e.g. soil moisture, surface hardness, crack width).
2. **Micro-climatic variables** (e.g. wind velocity vector, relative humidity, dew point).
3. **Player biometric or fatigue state** (e.g. heart rate, bowler cumulative overs spell strain).
*In accordance with project rules, no fabricated or simulated weather/pitch parameters have been introduced.*

---

## 6. Real-World Cricket Distribution Shift

An essential finding from the chronological match audit is the presence of an authentic **temporal distribution shift**:
- **Train Period (2022 to mid-2025)**: Batter runs averaged **1.334**, bowler runs conceded averaged **1.383**.
- **Test Period (2026)**: Batter runs rose to **1.443** (+8.1%), bowler runs conceded rose to **1.496** (+8.2%).

This accurately reflects modern cricket developments: higher batting aggression, modern powerplay exploitation, impact player adoption in league competitions, and progressive run-rate inflation. Models that generalize well must adapt to this secular shift without severe systematic bias.
