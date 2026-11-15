#!/usr/bin/env python3
'''
wpa_evaluation.py
Phase 2C: Win Probability & WPA Evaluation Pipeline.
Trains calibrated models on chronological splits, computes delivery WPA,
generates evaluation metrics (LogLoss, Brier, ROC-AUC, Calibration),
and writes all Phase 2C output deliverables.
'''
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score

from ml.phase2.win_probability import prepare_win_prob_features
from ml.phase2.wpa_engine import WPAEngine
from ml.phase2.wpa_attribution import attribute_delivery_wpa, aggregate_player_wpa

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCORED_FILE = BASE_DIR / 'output' / 'phase2' / 'pressure_scored_deliveries.csv'
MATCHES_FILE = BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv'
OUT_DIR = BASE_DIR / 'output' / 'phase2'

def run_wpa_pipeline():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Loading deliveries from {SCORED_FILE}...')
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    matches = pd.read_csv(MATCHES_FILE, low_memory=False)
    
    abandoned_ids = set(matches[matches.result.str.contains('Abandon|No result', case=False, na=False)].match_id)
    # Also exclude match 18532 (untied match with missing win_team_id)
    abandoned_ids.add(18532)
    print(f'Identified {len(abandoned_ids)} abandoned/incomplete matches to exclude from training.')
    
    # Filter valid deliveries for modeling: official scope, regular innings, non-abandoned
    valid_mask = (
        df['in_scope_competition'].fillna(False) &
        (~df['match_id'].isin(abandoned_ids)) &
        df['innings'].isin([1, 2])
    )
    modeling_df = df[valid_mask].copy()
    modeling_df = modeling_df.merge(matches[['match_id', 'win_team_id']], on='match_id', how='left')
    modeling_df['batting_team_won'] = (modeling_df['win_team_id_y'] == modeling_df['batting_team_id']).astype(int)
    
    # 1. Chronological Match Partition
    modeling_df['match_date'] = pd.to_datetime(modeling_df['match_date'])
    unique_matches = modeling_df[['match_id', 'match_date']].drop_duplicates().sort_values('match_date').reset_index(drop=True)
    
    n_matches = len(unique_matches)
    train_end = int(n_matches * 0.70)
    val_end = int(n_matches * 0.85)
    
    train_ids = set(unique_matches.iloc[:train_end]['match_id'])
    val_ids = set(unique_matches.iloc[train_end:val_end]['match_id'])
    test_ids = set(unique_matches.iloc[val_end:]['match_id'])
    
    d_start = unique_matches.iloc[0].match_date.strftime('%Y-%m-%d')
    d_train_end = unique_matches.iloc[train_end-1].match_date.strftime('%Y-%m-%d')
    d_val = unique_matches.iloc[val_end].match_date.strftime('%Y-%m-%d')
    d_test_end = unique_matches.iloc[-1].match_date.strftime('%Y-%m-%d')
    print(f'Matches split: Train={len(train_ids)} ({d_start} to {d_train_end}), Val={len(val_ids)}, Test={len(test_ids)} ({d_val} to {d_test_end})')
    
    train_df = modeling_df[modeling_df.match_id.isin(train_ids)]
    val_df = modeling_df[modeling_df.match_id.isin(val_ids)]
    test_df = modeling_df[modeling_df.match_id.isin(test_ids)]
    
    # 2. Train Engine
    engine = WPAEngine()
    engine.fit(train_df)
    
    # 3. Evaluate Out-of-Sample Test Set
    print('Evaluating Out-of-Sample Test Set...')
    test_chase = test_df[test_df['innings'] == 2].copy()
    test_chase_prep = prepare_win_prob_features(test_chase)
    test_chase_probs = engine.chase_model.predict_proba(test_chase_prep)
    y_test_chase = test_chase['batting_team_won'].values
    
    test_inn1 = test_df[test_df['innings'] == 1].copy()
    test_inn1_prep = prepare_win_prob_features(test_inn1)
    test_inn1_probs = engine.inn1_model.predict_proba(test_inn1_prep)
    y_test_inn1 = test_inn1['batting_team_won'].values
    
    # Baselines
    base_prob_chase = np.full_like(y_test_chase, train_df[train_df['innings'] == 2]['batting_team_won'].mean(), dtype=float)
    base_prob_inn1 = np.full_like(y_test_inn1, train_df[train_df['innings'] == 1]['batting_team_won'].mean(), dtype=float)
    
    eval_metrics = {
        'split': {
            'train_matches': len(train_ids),
            'val_matches': len(val_ids),
            'test_matches': len(test_ids),
            'train_deliveries': len(train_df),
            'test_deliveries': len(test_df),
            'test_period': f'{d_val} to {d_test_end}'
        },
        'chase_win_probability_model': {
            'model_log_loss': round(float(log_loss(y_test_chase, test_chase_probs)), 4),
            'baseline_log_loss': round(float(log_loss(y_test_chase, base_prob_chase)), 4),
            'model_brier_score': round(float(brier_score_loss(y_test_chase, test_chase_probs)), 4),
            'baseline_brier_score': round(float(brier_score_loss(y_test_chase, base_prob_chase)), 4),
            'model_roc_auc': round(float(roc_auc_score(y_test_chase, test_chase_probs)), 4),
            'calibration_mean_observed': round(float(np.mean(y_test_chase)), 4),
            'calibration_mean_predicted': round(float(np.mean(test_chase_probs)), 4)
        },
        'first_innings_win_probability_model': {
            'model_log_loss': round(float(log_loss(y_test_inn1, test_inn1_probs)), 4),
            'baseline_log_loss': round(float(log_loss(y_test_inn1, base_prob_inn1)), 4),
            'model_brier_score': round(float(brier_score_loss(y_test_inn1, test_inn1_probs)), 4),
            'baseline_brier_score': round(float(brier_score_loss(y_test_inn1, base_prob_inn1)), 4),
            'model_roc_auc': round(float(roc_auc_score(y_test_inn1, test_inn1_probs)), 4),
            'calibration_mean_observed': round(float(np.mean(y_test_inn1)), 4),
            'calibration_mean_predicted': round(float(np.mean(test_inn1_probs)), 4)
        }
    }
    
    with open(OUT_DIR / 'phase2c_evaluation.json', 'w') as f:
        json.dump(eval_metrics, f, indent=2)
    print('Saved phase2c_evaluation.json!')
    
    # 4. End-to-end WPA computation across all in-scope deliveries
    print('Scoring WPA across all in-scope deliveries...')
    full_in_scope = df[df.in_scope_competition.fillna(False)].copy()
    scored_wpa = engine.calculate_delivery_wpa(full_in_scope)
    
    # Export win_probability_predictions.csv
    pred_cols = [
        'match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num',
        'match_date', 'competition_scope', 'batting_team_name_clean', 'bowling_team_name_clean',
        'striker_id', 'striker_name_clean', 'bowler_id', 'bowler_name_clean',
        'innings_phase', 'pressure_score', 'pressure_tier',
        'score_before', 'wickets_lost_before', 'balls_remaining', 'target_runs',
        'runs_required', 'required_run_rate', 'current_run_rate',
        'p_win_before', 'p_win_after', 'delivery_wpa'
    ]
    scored_wpa[pred_cols].to_csv(OUT_DIR / 'win_probability_predictions.csv', index=False)
    print('Saved win_probability_predictions.csv!')
    
    # 5. Player Attribution
    print('Applying principled player attribution...')
    attr_wpa = attribute_delivery_wpa(scored_wpa)
    
    wpa_cols = pred_cols + [
        'actual_batter_runs', 'total_delivery_runs', 'is_wicket', 'bowler_wicket', 'extras_label',
        'batting_wpa', 'bowling_wpa', 'unattributed_wpa'
    ]
    # Ensure columns exist
    if 'actual_batter_runs' not in attr_wpa.columns:
        attr_wpa['actual_batter_runs'] = attr_wpa['batter_runs']
        
    attr_wpa[wpa_cols].to_csv(OUT_DIR / 'delivery_wpa.csv', index=False)
    print('Saved delivery_wpa.csv!')
    
    # 6. Aggregate to Player Level
    print('Aggregating player WPA summaries...')
    player_summary = aggregate_player_wpa(attr_wpa)
    player_summary.to_csv(OUT_DIR / 'player_wpa_summary.csv', index=False)
    print('Saved player_wpa_summary.csv!')
    
    print('Phase 2C pipeline completed successfully!')

if __name__ == '__main__':
    run_wpa_pipeline()
