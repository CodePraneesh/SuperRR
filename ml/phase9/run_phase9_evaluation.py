#!/usr/bin/env python3
"""
run_phase9_evaluation.py
Phase 9: Master Orchestrator for Context-Aware Machine Learning Model Comparison.
Trains, evaluates, and compares:
  - Naive Benchmark (Historical & Contextual Means)
  - Statistical Baseline (HistGradientBoosting)
  - CatBoost (Symmetric Oblivious Trees)
  - XGBoost (Depth-wise Second-Order Tree Boosting)
Computes match-grouped slice metrics, calibration deciles, contextual error analyses,
and experimental player ranking sensitivity under pressure.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error, log_loss, brier_score_loss, roc_auc_score

from ml.phase9.baseline_adapter import (
    CORE_FEATURE_COLS, EXTENDED_FEATURE_COLS, prepare_modeling_features,
    BaselineBatterRunsModel, BaselineBatterDismissalModel,
    BaselineBowlerRunsModel, BaselineBowlerWicketModel
)
from ml.phase9.catboost_experiment import (
    CatBoostBatterRunsModel, CatBoostBatterDismissalModel,
    CatBoostBowlerRunsModel, CatBoostBowlerWicketModel
)
from ml.phase9.xgboost_experiment import (
    XGBoostBatterRunsModel, XGBoostBatterDismissalModel,
    XGBoostBowlerRunsModel, XGBoostBowlerWicketModel
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCORED_FILE = BASE_DIR / 'output' / 'phase2' / 'pressure_scored_deliveries.csv'
MATCHES_FILE = BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv'
OUT_DIR = BASE_DIR / 'output' / 'phase9_ml_evaluation'
MODELS_DIR = OUT_DIR / 'models'

def calculate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    bias = float(np.mean(y_pred) - np.mean(y_true))
    # Pearson r and R2
    if np.std(y_pred) > 1e-9 and np.std(y_true) > 1e-9:
        r, _ = pearsonr(y_true, y_pred)
        r = float(r)
    else:
        r = 0.0
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_res = np.sum((y_true - y_pred) ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
    return {
        'mae': mae,
        'rmse': rmse,
        'bias': bias,
        'pearson_r': r,
        'r2': r2,
        'mean_observed': float(np.mean(y_true)),
        'mean_predicted': float(np.mean(y_pred))
    }

def calculate_classification_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    eps_prob = np.clip(y_prob, 1e-6, 1.0 - 1e-6)
    ll = float(log_loss(y_true, eps_prob))
    brier = float(brier_score_loss(y_true, eps_prob))
    try:
        auc = float(roc_auc_score(y_true, eps_prob))
    except Exception:
        auc = 0.5
    bias = float(np.mean(eps_prob) - np.mean(y_true))
    return {
        'log_loss': ll,
        'brier_score': brier,
        'roc_auc': auc,
        'bias': bias,
        'mean_observed': float(np.mean(y_true)),
        'mean_predicted': float(np.mean(eps_prob))
    }

def compute_decile_calibration(y_true: np.ndarray, y_prob: np.ndarray, model_name: str, target_name: str) -> list[dict]:
    df_cal = pd.DataFrame({'true': y_true, 'prob': y_prob})
    df_cal['bin'] = pd.qcut(df_cal['prob'], q=10, duplicates='drop')
    rows = []
    bin_num = 1
    for bin_interval, group in df_cal.groupby('bin', observed=False):
        n = len(group)
        obs_rate = group['true'].mean()
        pred_rate = group['prob'].mean()
        rows.append({
            'model': model_name,
            'target': target_name,
            'decile': bin_num,
            'bin_range': str(bin_interval),
            'samples': int(n),
            'observed_rate': float(obs_rate),
            'predicted_prob': float(pred_rate),
            'calibration_gap': float(pred_rate - obs_rate)
        })
        bin_num += 1
    return rows

def compute_brier_decomposition(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """
    Computes Murphy's Brier Score decomposition:
    Brier = Reliability - Resolution + Uncertainty
    Uncertainty = p_bar * (1 - p_bar)
    """
    p_bar = np.mean(y_true)
    uncertainty = float(p_bar * (1.0 - p_bar))
    total_brier = float(brier_score_loss(y_true, y_prob))
    
    # 10 bins
    bins = np.linspace(0.0, 1.0, 11)
    bin_idx = np.digitize(y_prob, bins) - 1
    bin_idx = np.clip(bin_idx, 0, 9)
    
    n_total = len(y_true)
    reliability = 0.0
    resolution = 0.0
    for k in range(10):
        mask = (bin_idx == k)
        n_k = np.sum(mask)
        if n_k > 0:
            p_k = np.mean(y_prob[mask])
            o_k = np.mean(y_true[mask])
            reliability += (n_k / n_total) * ((p_k - o_k) ** 2)
            resolution += (n_k / n_total) * ((o_k - p_bar) ** 2)
            
    return {
        'total_brier': total_brier,
        'uncertainty': uncertainty,
        'reliability': float(reliability),
        'resolution': float(resolution)
    }

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 80)
    print("STARTING PHASE 9: CONTEXT-AWARE ML MODEL COMPARISON")
    print("=" * 80)
    
    # 1. Load Data
    print(f"Loading data from {SCORED_FILE}...")
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    matches = pd.read_csv(MATCHES_FILE, low_memory=False)
    
    abandoned_ids = set(matches[matches.result.str.contains('Abandon|No result', case=False, na=False)].match_id)
    valid_mask = (
        df['in_scope_competition'].fillna(False) &
        (~df['match_id'].isin(abandoned_ids)) &
        df['innings'].isin([1, 2])
    )
    modeling_df = df[valid_mask].copy()
    modeling_df['match_date'] = pd.to_datetime(modeling_df['match_date'])
    
    # Feature preparation
    modeling_df = prepare_modeling_features(modeling_df)
    
    # Chronological match sorting
    unique_matches = modeling_df[['match_id', 'match_date']].drop_duplicates().sort_values('match_date').reset_index(drop=True)
    n_matches = len(unique_matches)
    train_end = int(n_matches * 0.70)
    val_end = int(n_matches * 0.85)
    
    train_ids = set(unique_matches.iloc[:train_end]['match_id'])
    val_ids = set(unique_matches.iloc[train_end:val_end]['match_id'])
    test_ids = set(unique_matches.iloc[val_end:]['match_id'])
    
    train_df = modeling_df[modeling_df.match_id.isin(train_ids)].copy()
    val_df = modeling_df[modeling_df.match_id.isin(val_ids)].copy()
    test_df = modeling_df[modeling_df.match_id.isin(test_ids)].copy()
    
    print(f"Dataset split: Train={len(train_df):,} balls ({len(train_ids)} matches), Val={len(val_df):,} balls ({len(val_ids)} matches), Test={len(test_df):,} balls ({len(test_ids)} matches)")
    
    # Target vectors on test
    y_test_bat_runs = test_df['batter_runs'].values
    y_test_bat_out = (test_df['dismissed_player_id'] == test_df['striker_id']).astype(int).values
    y_test_bowl_runs = test_df['bowler_runs_conceded'].values
    y_test_bowl_wkt = test_df['bowler_wicket'].astype(int).values
    
    # Training targets & means for Naive Baseline
    train_bat_runs_mean = float(train_df['batter_runs'].mean())
    train_bat_out_rate = float((train_df['dismissed_player_id'] == train_df['striker_id']).mean())
    train_bowl_runs_mean = float(train_df['bowler_runs_conceded'].mean())
    train_bowl_wkt_rate = float(train_df['bowler_wicket'].mean())
    
    # 2. FIT MODELS
    # A. Statistical Baseline
    print("\n--- Training Model A: Statistical Baseline (HistGradientBoosting) ---")
    t0 = time.time()
    base_bat_runs = BaselineBatterRunsModel()
    base_bat_runs.fit(train_df)
    joblib.dump(base_bat_runs.model, MODELS_DIR / 'baseline_batter_runs.joblib')
    
    base_bat_out = BaselineBatterDismissalModel()
    base_bat_out.fit(train_df)
    joblib.dump(base_bat_out.model, MODELS_DIR / 'baseline_batter_dismissal.joblib')
    
    base_bowl_runs = BaselineBowlerRunsModel()
    base_bowl_runs.fit(train_df)
    joblib.dump(base_bowl_runs.model, MODELS_DIR / 'baseline_bowler_runs.joblib')
    
    base_bowl_wkt = BaselineBowlerWicketModel()
    base_bowl_wkt.fit(train_df)
    joblib.dump(base_bowl_wkt.model, MODELS_DIR / 'baseline_bowler_wicket.joblib')
    base_train_time = time.time() - t0
    print(f"Statistical Baseline trained in {base_train_time:.2f} s")
    
    # B. CatBoost
    print("\n--- Training Model B: CatBoost ---")
    t0 = time.time()
    cb_bat_runs = CatBoostBatterRunsModel()
    cb_bat_runs.fit(train_df, val_df)
    cb_bat_runs.save(MODELS_DIR / 'catboost_batter_runs.cbm')
    
    cb_bat_out = CatBoostBatterDismissalModel()
    cb_bat_out.fit(train_df, val_df)
    cb_bat_out.save(MODELS_DIR / 'catboost_batter_dismissal.cbm')
    
    cb_bowl_runs = CatBoostBowlerRunsModel()
    cb_bowl_runs.fit(train_df, val_df)
    cb_bowl_runs.save(MODELS_DIR / 'catboost_bowler_runs.cbm')
    
    cb_bowl_wkt = CatBoostBowlerWicketModel()
    cb_bowl_wkt.fit(train_df, val_df)
    cb_bowl_wkt.save(MODELS_DIR / 'catboost_bowler_wicket.cbm')
    cb_train_time = time.time() - t0
    print(f"CatBoost trained in {cb_train_time:.2f} s")
    
    # C. XGBoost
    print("\n--- Training Model C: XGBoost ---")
    t0 = time.time()
    xgb_bat_runs = XGBoostBatterRunsModel()
    xgb_bat_runs.fit(train_df, val_df)
    xgb_bat_runs.save(MODELS_DIR / 'xgboost_batter_runs.json')
    
    xgb_bat_out = XGBoostBatterDismissalModel()
    xgb_bat_out.fit(train_df, val_df)
    xgb_bat_out.save(MODELS_DIR / 'xgboost_batter_dismissal.json')
    
    xgb_bowl_runs = XGBoostBowlerRunsModel()
    xgb_bowl_runs.fit(train_df, val_df)
    xgb_bowl_runs.save(MODELS_DIR / 'xgboost_bowler_runs.json')
    
    xgb_bowl_wkt = XGBoostBowlerWicketModel()
    xgb_bowl_wkt.fit(train_df, val_df)
    xgb_bowl_wkt.save(MODELS_DIR / 'xgboost_bowler_wicket.json')
    xgb_train_time = time.time() - t0
    print(f"XGBoost trained in {xgb_train_time:.2f} s")
    
    # 3. PREDICTIONS ON HELD-OUT TEST SET
    print("\nGenerating predictions on held-out test set...")
    # Naive predictions
    pred_naive_bat_runs = np.full(len(test_df), train_bat_runs_mean)
    prob_naive_bat_out = np.full(len(test_df), train_bat_out_rate)
    pred_naive_bowl_runs = np.full(len(test_df), train_bowl_runs_mean)
    prob_naive_bowl_wkt = np.full(len(test_df), train_bowl_wkt_rate)
    
    # Baseline predictions
    pred_base_bat_runs = base_bat_runs.predict(test_df)
    prob_base_bat_out = base_bat_out.predict_proba(test_df)
    pred_base_bowl_runs = base_bowl_runs.predict(test_df)
    prob_base_bowl_wkt = base_bowl_wkt.predict_proba(test_df)
    
    # CatBoost predictions
    pred_cb_bat_runs = cb_bat_runs.predict(test_df)
    prob_cb_bat_out = cb_bat_out.predict_proba(test_df)
    pred_cb_bowl_runs = cb_bowl_runs.predict(test_df)
    prob_cb_bowl_wkt = cb_bowl_wkt.predict_proba(test_df)
    
    # XGBoost predictions
    pred_xgb_bat_runs = xgb_bat_runs.predict(test_df)
    prob_xgb_bat_out = xgb_bat_out.predict_proba(test_df)
    pred_xgb_bowl_runs = xgb_bowl_runs.predict(test_df)
    prob_xgb_bowl_wkt = xgb_bowl_wkt.predict_proba(test_df)
    
    # Attach predictions to test_df for slice analysis
    test_df['pred_naive_bat_runs'] = pred_naive_bat_runs
    test_df['prob_naive_bat_out'] = prob_naive_bat_out
    test_df['pred_naive_bowl_runs'] = pred_naive_bowl_runs
    test_df['prob_naive_bowl_wkt'] = prob_naive_bowl_wkt
    
    test_df['pred_base_bat_runs'] = pred_base_bat_runs
    test_df['prob_base_bat_out'] = prob_base_bat_out
    test_df['pred_base_bowl_runs'] = pred_base_bowl_runs
    test_df['prob_base_bowl_wkt'] = prob_base_bowl_wkt
    
    test_df['pred_cb_bat_runs'] = pred_cb_bat_runs
    test_df['prob_cb_bat_out'] = prob_cb_bat_out
    test_df['pred_cb_bowl_runs'] = pred_cb_bowl_runs
    test_df['prob_cb_bowl_wkt'] = prob_cb_bowl_wkt
    
    test_df['pred_xgb_bat_runs'] = pred_xgb_bat_runs
    test_df['prob_xgb_bat_out'] = prob_xgb_bat_out
    test_df['pred_xgb_bowl_runs'] = pred_xgb_bowl_runs
    test_df['prob_xgb_bowl_wkt'] = prob_xgb_bowl_wkt
    
    # 4. SLICE EVALUATION MATRIX
    slices = {
        'Overall Test': np.ones(len(test_df), dtype=bool),
        'IPL Matches': (test_df['competition_scope'] == 'IPL').values,
        'T20I Matches': (test_df['competition_scope'] == 'T20I').values,
        'Powerplay (Overs 0-5)': (test_df['is_powerplay'] == 1).values,
        'Middle (Overs 6-15)': (test_df['is_middle'] == 1).values,
        'Death (Overs 16-19)': (test_df['is_death'] == 1).values,
        'Pressure (PI >= 50)': (test_df['pressure_score'] >= 50.0).values,
        'Non-Pressure (PI < 50)': (test_df['pressure_score'] < 50.0).values
    }
    
    eval_rows = []
    models_dict = {
        'Naive Baseline': {
            'bat_runs': pred_naive_bat_runs,
            'bat_out': prob_naive_bat_out,
            'bowl_runs': pred_naive_bowl_runs,
            'bowl_wkt': prob_naive_bowl_wkt
        },
        'Statistical Baseline': {
            'bat_runs': pred_base_bat_runs,
            'bat_out': prob_base_bat_out,
            'bowl_runs': pred_base_bowl_runs,
            'bowl_wkt': prob_base_bowl_wkt
        },
        'CatBoost': {
            'bat_runs': pred_cb_bat_runs,
            'bat_out': prob_cb_bat_out,
            'bowl_runs': pred_cb_bowl_runs,
            'bowl_wkt': prob_cb_bowl_wkt
        },
        'XGBoost': {
            'bat_runs': pred_xgb_bat_runs,
            'bat_out': prob_xgb_bat_out,
            'bowl_runs': pred_xgb_bowl_runs,
            'bowl_wkt': prob_xgb_bowl_wkt
        }
    }
    
    print("\nComputing slice metrics across all slices...")
    for slice_name, mask in slices.items():
        n_slice = int(np.sum(mask))
        y_br = y_test_bat_runs[mask]
        y_bo = y_test_bat_out[mask]
        y_bwr = y_test_bowl_runs[mask]
        y_bwk = y_test_bowl_wkt[mask]
        
        for m_name, m_preds in models_dict.items():
            # Batting runs
            reg_br = calculate_regression_metrics(y_br, m_preds['bat_runs'][mask])
            # Batting dismissal
            cls_bo = calculate_classification_metrics(y_bo, m_preds['bat_out'][mask])
            # Bowling runs
            reg_bwr = calculate_regression_metrics(y_bwr, m_preds['bowl_runs'][mask])
            # Bowling wicket
            cls_bwk = calculate_classification_metrics(y_bwk, m_preds['bowl_wkt'][mask])
            
            eval_rows.append({
                'slice': slice_name,
                'sample_size': n_slice,
                'model': m_name,
                # Batting runs
                'bat_runs_mae': reg_br['mae'],
                'bat_runs_rmse': reg_br['rmse'],
                'bat_runs_r2': reg_br['r2'],
                'bat_runs_bias': reg_br['bias'],
                # Batting dismissal
                'bat_out_log_loss': cls_bo['log_loss'],
                'bat_out_brier': cls_bo['brier_score'],
                'bat_out_auc': cls_bo['roc_auc'],
                'bat_out_bias': cls_bo['bias'],
                # Bowling runs
                'bowl_runs_mae': reg_bwr['mae'],
                'bowl_runs_rmse': reg_bwr['rmse'],
                'bowl_runs_r2': reg_bwr['r2'],
                'bowl_runs_bias': reg_bwr['bias'],
                # Bowling wicket
                'bowl_wkt_log_loss': cls_bwk['log_loss'],
                'bowl_wkt_brier': cls_bwk['brier_score'],
                'bowl_wkt_auc': cls_bwk['roc_auc'],
                'bowl_wkt_bias': cls_bwk['bias']
            })
            
    eval_df = pd.DataFrame(eval_rows)
    eval_csv_path = OUT_DIR / 'match_grouped_evaluation.csv'
    eval_df.to_csv(eval_csv_path, index=False)
    print(f"Saved evaluation matrix to {eval_csv_path}")
    
    # 5. CALIBRATION REPORT & DECILES
    print("\nComputing calibration deciles and Brier score decompositions...")
    cal_rows = []
    for m_name in ['Statistical Baseline', 'CatBoost', 'XGBoost']:
        cal_rows.extend(compute_decile_calibration(y_test_bat_out, models_dict[m_name]['bat_out'], m_name, 'Batter Dismissal Prob'))
        cal_rows.extend(compute_decile_calibration(y_test_bowl_wkt, models_dict[m_name]['bowl_wkt'], m_name, 'Bowler Wicket Prob'))
    cal_df = pd.DataFrame(cal_rows)
    cal_df.to_csv(OUT_DIR / 'calibration_deciles.csv', index=False)
    
    # Brier decompositions
    brier_decomp = {}
    for m_name in ['Statistical Baseline', 'CatBoost', 'XGBoost']:
        brier_decomp[m_name] = {
            'bat_dismissal': compute_brier_decomposition(y_test_bat_out, models_dict[m_name]['bat_out']),
            'bowler_wicket': compute_brier_decomposition(y_test_bowl_wkt, models_dict[m_name]['bowl_wkt'])
        }
    with open(OUT_DIR / 'brier_decomposition.json', 'w', encoding='utf-8') as f:
        json.dump(brier_decomp, f, indent=2)
    
    # 6. BASELINE MODEL EVALUATION JSON (Deliverable 2)
    base_overall = eval_df[(eval_df['slice'] == 'Overall Test') & (eval_df['model'] == 'Statistical Baseline')].iloc[0]
    naive_overall = eval_df[(eval_df['slice'] == 'Overall Test') & (eval_df['model'] == 'Naive Baseline')].iloc[0]
    
    baseline_eval_json = {
        "model_architecture": "Statistical Baseline (HistGradientBoosting)",
        "split": {
            "train_matches": len(train_ids),
            "val_matches": len(val_ids),
            "test_matches": len(test_ids),
            "train_deliveries": len(train_df),
            "test_deliveries": len(test_df),
            "test_period": "2026-02-01 to 2026-11-01"
        },
        "training_time_seconds": round(base_train_time, 2),
        "batter_expected_runs": {
            "model_mae": round(float(base_overall['bat_runs_mae']), 4),
            "baseline_mae": round(float(naive_overall['bat_runs_mae']), 4),
            "model_rmse": round(float(base_overall['bat_runs_rmse']), 4),
            "baseline_rmse": round(float(naive_overall['bat_runs_rmse']), 4),
            "rmse_improvement_pct": round(float((1.0 - base_overall['bat_runs_rmse'] / naive_overall['bat_runs_rmse']) * 100), 2),
            "bias": round(float(base_overall['bat_runs_bias']), 4)
        },
        "batter_dismissal_prob": {
            "model_log_loss": round(float(base_overall['bat_out_log_loss']), 4),
            "baseline_log_loss": round(float(naive_overall['bat_out_log_loss']), 4),
            "model_brier_score": round(float(base_overall['bat_out_brier']), 5),
            "baseline_brier_score": round(float(naive_overall['bat_out_brier']), 5),
            "roc_auc": round(float(base_overall['bat_out_auc']), 4),
            "calibration_mean_observed": round(float(np.mean(y_test_bat_out)), 4),
            "calibration_mean_predicted": round(float(np.mean(pred_base_bat_runs)), 4)
        },
        "bowler_expected_runs": {
            "model_mae": round(float(base_overall['bowl_runs_mae']), 4),
            "baseline_mae": round(float(naive_overall['bowl_runs_mae']), 4),
            "model_rmse": round(float(base_overall['bowl_runs_rmse']), 4),
            "baseline_rmse": round(float(naive_overall['bowl_runs_rmse']), 4),
            "rmse_improvement_pct": round(float((1.0 - base_overall['bowl_runs_rmse'] / naive_overall['bowl_runs_rmse']) * 100), 2),
            "bias": round(float(base_overall['bowl_runs_bias']), 4)
        },
        "bowler_wicket_prob": {
            "model_log_loss": round(float(base_overall['bowl_wkt_log_loss']), 4),
            "baseline_log_loss": round(float(naive_overall['bowl_wkt_log_loss']), 4),
            "model_brier_score": round(float(base_overall['bowl_wkt_brier']), 5),
            "baseline_brier_score": round(float(naive_overall['bowl_wkt_brier']), 5),
            "roc_auc": round(float(base_overall['bowl_wkt_auc']), 4),
            "calibration_mean_observed": round(float(np.mean(y_test_bowl_wkt)), 4),
            "calibration_mean_predicted": round(float(np.mean(prob_base_bowl_wkt)), 4)
        }
    }
    with open(OUT_DIR / 'baseline_model_evaluation.json', 'w', encoding='utf-8') as f:
        json.dump(baseline_eval_json, f, indent=2)
    print("Saved baseline_model_evaluation.json")

    # 7. FEATURE IMPORTANCES
    feat_imp = {
        'catboost': {
            'bat_runs': cb_bat_runs.get_feature_importance(),
            'bat_out': cb_bat_out.get_feature_importance(),
            'bowl_runs': cb_bowl_runs.get_feature_importance(),
            'bowl_wkt': cb_bowl_wkt.get_feature_importance()
        },
        'xgboost': {
            'bat_runs': xgb_bat_runs.get_feature_importance(),
            'bat_out': xgb_bat_out.get_feature_importance(),
            'bowl_runs': xgb_bowl_runs.get_feature_importance(),
            'bowl_wkt': xgb_bowl_wkt.get_feature_importance()
        }
    }
    with open(OUT_DIR / 'feature_importances.json', 'w', encoding='utf-8') as f:
        json.dump(feat_imp, f, indent=2)
        
    # 8. EXPERIMENTAL PLAYER RANKING SENSITIVITY (Section 7)
    print("\n--- Computing Experimental Player Ranking Sensitivity under Pressure ---")
    # Residuals on test deliveries under pressure
    # Wicket replacement weight = 15.0 (official Phase 2B weight)
    W_WKT = 15.0
    
    # Batting residual delta: (actual_runs - exp_runs) - W_WKT * (actual_out - exp_out)
    test_df['delta_base_bat'] = (test_df['batter_runs'] - test_df['pred_base_bat_runs']) - W_WKT * (y_test_bat_out - test_df['prob_base_bat_out'])
    test_df['delta_cb_bat'] = (test_df['batter_runs'] - test_df['pred_cb_bat_runs']) - W_WKT * (y_test_bat_out - test_df['prob_cb_bat_out'])
    test_df['delta_xgb_bat'] = (test_df['batter_runs'] - test_df['pred_xgb_bat_runs']) - W_WKT * (y_test_bat_out - test_df['prob_xgb_bat_out'])
    
    # Bowling residual delta: (exp_runs - actual_runs) + W_WKT * (actual_wkt - exp_wkt)
    test_df['delta_base_bowl'] = (test_df['pred_base_bowl_runs'] - test_df['bowler_runs_conceded']) + W_WKT * (y_test_bowl_wkt - test_df['prob_base_bowl_wkt'])
    test_df['delta_cb_bowl'] = (test_df['pred_cb_bowl_runs'] - test_df['bowler_runs_conceded']) + W_WKT * (y_test_bowl_wkt - test_df['prob_cb_bowl_wkt'])
    test_df['delta_xgb_bowl'] = (test_df['pred_xgb_bowl_runs'] - test_df['bowler_runs_conceded']) + W_WKT * (y_test_bowl_wkt - test_df['prob_xgb_bowl_wkt'])
    
    # Focus on pressure deliveries (PI >= 50)
    pressure_test = test_df[test_df['pressure_score'] >= 50.0].copy()
    
    # Batter Aggregation
    bat_agg = pressure_test.groupby(['striker_id', 'striker_name_clean']).agg(
        balls=('batter_runs', 'count'),
        actual_runs=('batter_runs', 'sum'),
        base_delta=('delta_base_bat', 'mean'),
        cb_delta=('delta_cb_bat', 'mean'),
        xgb_delta=('delta_xgb_bat', 'mean')
    ).reset_index()
    # Filter for qualified batters in held-out test sample (min 30 pressure balls in test period)
    qual_bat = bat_agg[bat_agg['balls'] >= 30].copy()
    qual_bat['rank_base'] = qual_bat['base_delta'].rank(ascending=False, method='min').astype(int)
    qual_bat['rank_cb'] = qual_bat['cb_delta'].rank(ascending=False, method='min').astype(int)
    qual_bat['rank_xgb'] = qual_bat['xgb_delta'].rank(ascending=False, method='min').astype(int)
    qual_bat = qual_bat.sort_values('rank_base').reset_index(drop=True)
    
    # Bowler Aggregation
    bowl_agg = pressure_test.groupby(['bowler_id', 'bowler_name_clean']).agg(
        balls=('bowler_runs_conceded', 'count'),
        runs_conceded=('bowler_runs_conceded', 'sum'),
        wickets=('bowler_wicket', 'sum'),
        base_delta=('delta_base_bowl', 'mean'),
        cb_delta=('delta_cb_bowl', 'mean'),
        xgb_delta=('delta_xgb_bowl', 'mean')
    ).reset_index()
    # Filter for qualified bowlers in held-out test sample (min 24 pressure balls in test period)
    qual_bowl = bowl_agg[bowl_agg['balls'] >= 24].copy()
    qual_bowl['rank_base'] = qual_bowl['base_delta'].rank(ascending=False, method='min').astype(int)
    qual_bowl['rank_cb'] = qual_bowl['cb_delta'].rank(ascending=False, method='min').astype(int)
    qual_bowl['rank_xgb'] = qual_bowl['xgb_delta'].rank(ascending=False, method='min').astype(int)
    qual_bowl = qual_bowl.sort_values('rank_base').reset_index(drop=True)
    
    # Spearman rank correlations
    spearman_bat_base_cb, _ = spearmanr(qual_bat['rank_base'], qual_bat['rank_cb'])
    spearman_bat_base_xgb, _ = spearmanr(qual_bat['rank_base'], qual_bat['rank_xgb'])
    spearman_bat_cb_xgb, _ = spearmanr(qual_bat['rank_cb'], qual_bat['rank_xgb'])
    
    spearman_bowl_base_cb, _ = spearmanr(qual_bowl['rank_base'], qual_bowl['rank_cb'])
    spearman_bowl_base_xgb, _ = spearmanr(qual_bowl['rank_base'], qual_bowl['rank_xgb'])
    spearman_bowl_cb_xgb, _ = spearmanr(qual_bowl['rank_cb'], qual_bowl['rank_xgb'])
    
    # Top 10 overlap
    top10_bat_base = set(qual_bat.sort_values('rank_base').head(10)['striker_id'])
    top10_bat_cb = set(qual_bat.sort_values('rank_cb').head(10)['striker_id'])
    top10_bat_xgb = set(qual_bat.sort_values('rank_xgb').head(10)['striker_id'])
    
    top10_bowl_base = set(qual_bowl.sort_values('rank_base').head(10)['bowler_id'])
    top10_bowl_cb = set(qual_bowl.sort_values('rank_cb').head(10)['bowler_id'])
    top10_bowl_xgb = set(qual_bowl.sort_values('rank_xgb').head(10)['bowler_id'])
    
    sensitivity_summary = {
        'batting': {
            'qualified_players_in_test_pressure': len(qual_bat),
            'spearman_rank_correlation': {
                'baseline_vs_catboost': round(float(spearman_bat_base_cb), 4),
                'baseline_vs_xgboost': round(float(spearman_bat_base_xgb), 4),
                'catboost_vs_xgboost': round(float(spearman_bat_cb_xgb), 4)
            },
            'top_10_overlap_count': {
                'baseline_and_catboost': len(top10_bat_base & top10_bat_cb),
                'baseline_and_xgboost': len(top10_bat_base & top10_bat_xgb),
                'catboost_and_xgboost': len(top10_bat_cb & top10_bat_xgb)
            }
        },
        'bowling': {
            'qualified_players_in_test_pressure': len(qual_bowl),
            'spearman_rank_correlation': {
                'baseline_vs_catboost': round(float(spearman_bowl_base_cb), 4),
                'baseline_vs_xgboost': round(float(spearman_bowl_base_xgb), 4),
                'catboost_vs_xgboost': round(float(spearman_bowl_cb_xgb), 4)
            },
            'top_10_overlap_count': {
                'baseline_and_catboost': len(top10_bowl_base & top10_bowl_cb),
                'baseline_and_xgboost': len(top10_bowl_base & top10_bowl_xgb),
                'catboost_and_xgboost': len(top10_bowl_cb & top10_bowl_xgb)
            }
        }
    }
    with open(OUT_DIR / 'ranking_sensitivity_summary.json', 'w', encoding='utf-8') as f:
        json.dump(sensitivity_summary, f, indent=2)
        
    qual_bat.to_csv(OUT_DIR / 'experimental_batters_ranking_comparison.csv', index=False)
    qual_bowl.to_csv(OUT_DIR / 'experimental_bowlers_ranking_comparison.csv', index=False)
    print("Saved player rankings comparison CSVs and sensitivity summary.")

    print("\n" + "=" * 80)
    print("PHASE 9 MASTER EVALUATION RUN COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == '__main__':
    main()
