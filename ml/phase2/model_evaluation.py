#!/usr/bin/env python3
'''
model_evaluation.py
Phase 2B: Chronological Model Training, Evaluation, and Delivery Inference Pipeline.
Generates evaluation metrics (MAE, RMSE, LogLoss, Brier) against baselines and writes all Phase 2B outputs.
'''
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, log_loss, brier_score_loss

from ml.phase2.expected_batting import prepare_batting_features, BatterExpectedRunsModel, BatterDismissalModel
from ml.phase2.expected_bowling import prepare_bowling_features, BowlerExpectedRunsModel, BowlerWicketModel
from ml.phase2.performance_delta import compute_batting_performance_residuals, compute_bowling_performance_residuals
from ml.phase2.player_performance_aggregation import aggregate_batter_performance, aggregate_bowler_performance

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCORED_FILE = BASE_DIR / 'output' / 'phase2' / 'pressure_scored_deliveries.csv'
MATCHES_FILE = BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv'
OUT_DIR = BASE_DIR / 'output' / 'phase2'

def run_evaluation_and_inference():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Loading deliveries from {SCORED_FILE}...')
    df = pd.read_csv(SCORED_FILE, low_memory=False)
    matches = pd.read_csv(MATCHES_FILE, low_memory=False)
    
    abandoned_ids = set(matches[matches.result.str.contains('Abandon|No result', case=False, na=False)].match_id)
    print(f'Identified {len(abandoned_ids)} abandoned matches to exclude from model training.')
    
    # Filter valid deliveries for modeling: official scope, regular innings, non-abandoned
    valid_mask = (
        df['in_scope_competition'].fillna(False) &
        (~df['match_id'].isin(abandoned_ids)) &
        df['innings'].isin([1, 2])
    )
    modeling_df = df[valid_mask].copy()
    
    # 1. Chronological Match Split
    # Sort distinct match IDs chronologically by match_date
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
    
    # Prepare features
    b_df = prepare_batting_features(modeling_df)
    bw_df = prepare_bowling_features(modeling_df)
    
    train_b = b_df[b_df.match_id.isin(train_ids)]
    test_b = b_df[b_df.match_id.isin(test_ids)]
    
    train_bw = bw_df[bw_df.match_id.isin(train_ids)]
    test_bw = bw_df[bw_df.match_id.isin(test_ids)]
    
    # 2. Train Batting Models
    print('Training Batter Expected Runs Model...')
    bat_runs_model = BatterExpectedRunsModel()
    bat_runs_model.fit(train_b)
    
    print('Training Batter Dismissal Probability Model...')
    bat_out_model = BatterDismissalModel()
    bat_out_model.fit(train_b)
    
    # 3. Train Bowling Models
    print('Training Bowler Expected Runs Conceded Model...')
    bowl_runs_model = BowlerExpectedRunsModel()
    bowl_runs_model.fit(train_bw)
    
    print('Training Bowler Wicket Probability Model...')
    bowl_wkt_model = BowlerWicketModel()
    bowl_wkt_model.fit(train_bw)
    
    # 4. Out-of-Sample Evaluation on Chronological Test Set
    y_test_bat_runs = test_b['batter_runs'].values
    pred_test_bat_runs = bat_runs_model.predict(test_b)
    baseline_bat_runs = np.full_like(y_test_bat_runs, train_b['batter_runs'].mean())
    
    y_test_bat_out = (test_b['dismissed_player_id'] == test_b['striker_id']).astype(int).values
    prob_test_bat_out = bat_out_model.predict_proba(test_b)
    base_prob_bat_out = np.full_like(y_test_bat_out, (train_b['dismissed_player_id'] == train_b['striker_id']).mean(), dtype=float)
    
    y_test_bowl_runs = test_bw['bowler_runs_conceded'].values
    pred_test_bowl_runs = bowl_runs_model.predict(test_bw)
    baseline_bowl_runs = np.full_like(y_test_bowl_runs, train_bw['bowler_runs_conceded'].mean())
    
    y_test_bowl_wkt = test_bw['bowler_wicket'].astype(int).values
    prob_test_bowl_wkt = bowl_wkt_model.predict_proba(test_bw)
    base_prob_bowl_wkt = np.full_like(y_test_bowl_wkt, train_bw['bowler_wicket'].astype(int).mean(), dtype=float)
    
    eval_metrics = {
        'split': {
            'train_matches': len(train_ids),
            'val_matches': len(val_ids),
            'test_matches': len(test_ids),
            'train_deliveries': len(train_b),
            'test_deliveries': len(test_b),
            'test_period': f'{d_val} to {d_test_end}'
        },
        'batter_expected_runs': {
            'model_mae': round(float(mean_absolute_error(y_test_bat_runs, pred_test_bat_runs)), 4),
            'baseline_mae': round(float(mean_absolute_error(y_test_bat_runs, baseline_bat_runs)), 4),
            'model_rmse': round(float(np.sqrt(mean_squared_error(y_test_bat_runs, pred_test_bat_runs))), 4),
            'baseline_rmse': round(float(np.sqrt(mean_squared_error(y_test_bat_runs, baseline_bat_runs))), 4),
            'mae_improvement_pct': round(float((mean_absolute_error(y_test_bat_runs, baseline_bat_runs) - mean_absolute_error(y_test_bat_runs, pred_test_bat_runs)) / mean_absolute_error(y_test_bat_runs, baseline_bat_runs) * 100), 2)
        },
        'batter_dismissal_prob': {
            'model_log_loss': round(float(log_loss(y_test_bat_out, prob_test_bat_out)), 4),
            'baseline_log_loss': round(float(log_loss(y_test_bat_out, base_prob_bat_out)), 4),
            'model_brier_score': round(float(brier_score_loss(y_test_bat_out, prob_test_bat_out)), 5),
            'baseline_brier_score': round(float(brier_score_loss(y_test_bat_out, base_prob_bat_out)), 5),
            'calibration_mean_observed': round(float(np.mean(y_test_bat_out)), 4),
            'calibration_mean_predicted': round(float(np.mean(prob_test_bat_out)), 4)
        },
        'bowler_expected_runs': {
            'model_mae': round(float(mean_absolute_error(y_test_bowl_runs, pred_test_bowl_runs)), 4),
            'baseline_mae': round(float(mean_absolute_error(y_test_bowl_runs, baseline_bowl_runs)), 4),
            'model_rmse': round(float(np.sqrt(mean_squared_error(y_test_bowl_runs, pred_test_bowl_runs))), 4),
            'baseline_rmse': round(float(np.sqrt(mean_squared_error(y_test_bowl_runs, baseline_bowl_runs))), 4),
            'mae_improvement_pct': round(float((mean_absolute_error(y_test_bowl_runs, baseline_bowl_runs) - mean_absolute_error(y_test_bowl_runs, pred_test_bowl_runs)) / mean_absolute_error(y_test_bowl_runs, baseline_bowl_runs) * 100), 2)
        },
        'bowler_wicket_prob': {
            'model_log_loss': round(float(log_loss(y_test_bowl_wkt, prob_test_bowl_wkt)), 4),
            'baseline_log_loss': round(float(log_loss(y_test_bowl_wkt, base_prob_bowl_wkt)), 4),
            'model_brier_score': round(float(brier_score_loss(y_test_bowl_wkt, prob_test_bowl_wkt)), 5),
            'baseline_brier_score': round(float(brier_score_loss(y_test_bowl_wkt, base_prob_bowl_wkt)), 5),
            'calibration_mean_observed': round(float(np.mean(y_test_bowl_wkt)), 4),
            'calibration_mean_predicted': round(float(np.mean(prob_test_bowl_wkt)), 4)
        }
    }
    
    with open(OUT_DIR / 'phase2b_model_evaluation.json', 'w') as f:
        json.dump(eval_metrics, f, indent=2)
    print('Saved phase2b_model_evaluation.json!')
    
    # 5. Full Dataset Delivery Inference (for in-scope deliveries)
    print('Computing delivery expectations across all in-scope deliveries...')
    full_in_scope = df[df.in_scope_competition.fillna(False)].copy()
    full_b = prepare_batting_features(full_in_scope)
    full_bw = prepare_bowling_features(full_in_scope)
    
    # Predict batting
    full_b['expected_batter_runs'] = bat_runs_model.predict(full_b)
    full_b['expected_dismissal_prob'] = bat_out_model.predict_proba(full_b)
    full_b['actual_batter_runs'] = full_b['batter_runs']
    full_b['actual_dismissal_outcome'] = (full_b['dismissed_player_id'] == full_b['striker_id']).astype(int)
    
    batter_delivery_df = compute_batting_performance_residuals(full_b)
    batter_cols_to_keep = [
        'match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num',
        'match_date', 'competition_scope', 'batting_team_name_clean', 'bowling_team_name_clean',
        'striker_id', 'striker_name_clean', 'bowler_id', 'bowler_name_clean',
        'innings_phase', 'pressure_score', 'pressure_tier',
        'actual_batter_runs', 'expected_batter_runs', 'batting_run_residual',
        'actual_dismissal_outcome', 'expected_dismissal_prob', 'batting_dismissal_residual',
        'pressure_multiplier', 'pressure_adjusted_batting_run_delta', 'pressure_adjusted_batting_out_delta'
    ]
    batter_delivery_out = batter_delivery_df[batter_cols_to_keep].copy()
    batter_delivery_out.to_csv(OUT_DIR / 'batter_delivery_expectations.csv', index=False)
    print('Saved batter_delivery_expectations.csv!')
    
    # Predict bowling
    full_bw['expected_runs_conceded'] = bowl_runs_model.predict(full_bw)
    full_bw['expected_wicket_prob'] = bowl_wkt_model.predict_proba(full_bw)
    full_bw['actual_runs_conceded'] = full_bw['bowler_runs_conceded']
    full_bw['actual_wicket_outcome'] = full_bw['bowler_wicket'].astype(int)
    
    bowler_delivery_df = compute_bowling_performance_residuals(full_bw)
    bowler_cols_to_keep = [
        'match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num',
        'match_date', 'competition_scope', 'batting_team_name_clean', 'bowling_team_name_clean',
        'striker_id', 'striker_name_clean', 'bowler_id', 'bowler_name_clean',
        'innings_phase', 'pressure_score', 'pressure_tier',
        'actual_runs_conceded', 'expected_runs_conceded', 'bowling_run_residual',
        'actual_wicket_outcome', 'expected_wicket_prob', 'bowling_wicket_residual',
        'pressure_multiplier', 'pressure_adjusted_bowling_run_delta', 'pressure_adjusted_bowling_wicket_delta'
    ]
    bowler_delivery_out = bowler_delivery_df[bowler_cols_to_keep].copy()
    bowler_delivery_out.to_csv(OUT_DIR / 'bowler_delivery_expectations.csv', index=False)
    print('Saved bowler_delivery_expectations.csv!')
    
    # 6. Aggregate to Player Level
    print('Aggregating player performance summaries...')
    batter_summary = aggregate_batter_performance(batter_delivery_df)
    batter_summary.to_csv(OUT_DIR / 'batter_performance_summary.csv', index=False)
    print('Saved batter_performance_summary.csv!')
    
    bowler_summary = aggregate_bowler_performance(bowler_delivery_df)
    bowler_summary.to_csv(OUT_DIR / 'bowler_performance_summary.csv', index=False)
    print('Saved bowler_performance_summary.csv!')
    
    print('All Phase 2B model training, evaluation, and aggregations completed successfully!')

if __name__ == '__main__':
    run_evaluation_and_inference()
