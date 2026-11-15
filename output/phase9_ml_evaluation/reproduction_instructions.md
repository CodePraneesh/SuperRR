# SupeRR Intelligence — Phase 9: Experiment Reproduction Instructions

## 1. Overview & System Requirements

This document provides exact, deterministic commands to reproduce the Phase 9 Context-Aware Machine Learning Model Comparison from raw data files to final evaluation tables and reports.

### Environment Specification
- **Operating System**: Windows / Linux / macOS
- **Python**: 3.10+ (tested on Python 3.14.0)
- **Required Packages**:
  ```bash
  pip install scikit-learn>=1.4.0 xgboost>=2.0.0 catboost>=1.2.0 pandas>=2.0.0 numpy>=1.26.0 scipy>=1.12.0 joblib>=1.3.0
  ```

---

## 2. Source Files & Verification

Ensure the following pre-processed data files exist at the root of `SupeRR_Phase1`:
1. `output/phase2/pressure_scored_deliveries.csv` (SHA-256: `78cbdb7045b6ad64b971a8fb1d7646543bda71e98bb4b7ef432709e9921612df`)
2. `output/processed/matches_enriched.csv` (SHA-256: `d9426d03d3db25e6561fcb2ca3a9e320f772e0fa4c13a696bfbe29837c732009`)

---

## 3. Step-by-Step Reproduction Pipeline

Navigate to the project root directory:
```bash
cd SupeRR_Intelligence_Phase1/SupeRR_Phase1
```

### Step 1: Run the Dataset and Feature Audit
Verifies cryptographic checksums, checks chronological match splits (569 train, 122 val, 122 test), verifies non-leakage invariants, and generates `dataset_and_feature_audit.md`:
```bash
python -m ml.phase9.dataset_audit
```
*Expected runtime: ~12 seconds.*

---

### Step 2: Execute the Master Model Training and Evaluation Pipeline
Trains all 12 models (Statistical Baseline, CatBoost, XGBoost across 4 targets), logs training durations, computes out-of-sample test metrics across 8 match slices, generates 10-decile calibration tables and Brier decompositions, evaluates player ranking sensitivity under pressure, and serializes trained models:
```bash
python -m ml.phase9.run_phase9_evaluation
```
*Expected runtime: ~35 seconds.*

Output artifacts generated:
- `output/phase9_ml_evaluation/baseline_model_evaluation.json`
- `output/phase9_ml_evaluation/match_grouped_evaluation.csv`
- `output/phase9_ml_evaluation/calibration_deciles.csv`
- `output/phase9_ml_evaluation/brier_decomposition.json`
- `output/phase9_ml_evaluation/feature_importances.json`
- `output/phase9_ml_evaluation/ranking_sensitivity_summary.json`
- `output/phase9_ml_evaluation/experimental_batters_ranking_comparison.csv`
- `output/phase9_ml_evaluation/experimental_bowlers_ranking_comparison.csv`
- `output/phase9_ml_evaluation/models/` (contains serialized `.joblib`, `.cbm`, and `.json` model files)

---

### Step 3: Run the Automated Phase 9 Validation Test Suite
Executes the comprehensive automated test suite verifying file existence, non-leakage, split integrity, metric validity, and preservation rules:
```bash
python -m unittest tests/test_phase9_validation.py -v
```
*Expected result: 100% tests passing.*

---

## 4. Hyperparameter Reference Table

| Model | Target | Library Class | Primary Hyperparameters | Random Seed |
| :--- | :--- | :--- | :--- | :---: |
| **Baseline** | Batter Runs | `HistGradientBoostingRegressor` | `max_iter=150, lr=0.05, max_depth=5, min_leaf=30, l2=1.0` | 42 |
| **Baseline** | Batter Dismissal | `HistGradientBoostingClassifier` | `max_iter=120, lr=0.04, max_depth=4, min_leaf=40, l2=2.0` | 42 |
| **Baseline** | Bowler Runs | `HistGradientBoostingRegressor` | `max_iter=150, lr=0.05, max_depth=5, min_leaf=30, l2=1.0` | 42 |
| **Baseline** | Bowler Wickets | `HistGradientBoostingClassifier` | `max_iter=120, lr=0.04, max_depth=4, min_leaf=40, l2=2.0` | 42 |
| **CatBoost** | Batter Runs | `CatBoostRegressor` | `iterations=250, lr=0.05, depth=6, l2_reg=3.0, early_stopping=25` | 42 |
| **CatBoost** | Batter Dismissal | `CatBoostClassifier` | `iterations=200, lr=0.04, depth=5, l2_reg=4.0, early_stopping=20` | 42 |
| **CatBoost** | Bowler Runs | `CatBoostRegressor` | `iterations=250, lr=0.05, depth=6, l2_reg=3.0, early_stopping=25` | 42 |
| **CatBoost** | Bowler Wickets | `CatBoostClassifier` | `iterations=200, lr=0.04, depth=5, l2_reg=4.0, early_stopping=20` | 42 |
| **XGBoost** | Batter Runs | `XGBRegressor` | `n_est=250, lr=0.05, depth=5, min_child=30, reg_lambda=2.0, subsample=0.85, colsample=0.85` | 42 |
| **XGBoost** | Batter Dismissal | `XGBClassifier` | `n_est=200, lr=0.04, depth=4, min_child=40, reg_lambda=3.0, subsample=0.85, colsample=0.85` | 42 |
| **XGBoost** | Bowler Runs | `XGBRegressor` | `n_est=250, lr=0.05, depth=5, min_child=30, reg_lambda=2.0, subsample=0.85, colsample=0.85` | 42 |
| **XGBoost** | Bowler Wickets | `XGBClassifier` | `n_est=200, lr=0.04, depth=4, min_child=40, reg_lambda=3.0, subsample=0.85, colsample=0.85` | 42 |
