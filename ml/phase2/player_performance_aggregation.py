#!/usr/bin/env python3
'''
player_performance_aggregation.py
Phase 2B: Player-Level Aggregation with Bayesian Shrinkage & Sample Reliability Tiers.
Separates IPL and T20I without hiding small-sample players.
'''
from __future__ import annotations
import numpy as np
import pandas as pd

def aggregate_batter_performance(df: pd.DataFrame, m_prior: float = 30.0) -> pd.DataFrame:
    '''
    Aggregates delivery-level batting residuals to player level.
    Applies empirical Bayes shrinkage towards context neutral mean (0.0).
    m_prior: pseudo-sample weight for shrinkage (30 balls).
    '''
    d = df.copy()
    d['is_pressure'] = d['pressure_score'].ge(50.0) # High pressure definition (>50 score)
    
    records = []
    for (pid, pname, scope), grp in d.groupby(['striker_id', 'striker_name_clean', 'competition_scope']):
        total_balls = len(grp)
        actual_runs = grp['actual_batter_runs'].sum()
        exp_runs = grp['expected_batter_runs'].sum()
        raw_run_delta = grp['batting_run_residual'].sum()
        pressure_adj_run_delta = grp['pressure_adjusted_batting_run_delta'].sum()
        
        actual_outs = grp['actual_dismissal_outcome'].sum()
        exp_outs = grp['expected_dismissal_prob'].sum()
        out_delta = grp['batting_dismissal_residual'].sum()
        
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        p_run_delta = p_grp['batting_run_residual'].sum() if p_balls > 0 else 0.0
        p_adj_run_delta = p_grp['pressure_adjusted_batting_run_delta'].sum() if p_balls > 0 else 0.0
        
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        np_run_delta = np_grp['batting_run_residual'].sum() if np_balls > 0 else 0.0
        
        matches = grp['match_id'].nunique()
        
        # Bayesian Shrinkage on run residual per ball
        # shrinkage_factor = N / (N + m_prior)
        # raw mean residual per ball = raw_run_delta / total_balls
        # shrunk residual per ball = raw mean * shrinkage_factor
        shrinkage_weight = total_balls / (total_balls + m_prior)
        mean_run_delta_per_ball = raw_run_delta / total_balls
        shrunk_run_delta_per_ball = mean_run_delta_per_ball * shrinkage_weight
        shrunk_total_run_delta = shrunk_run_delta_per_ball * total_balls
        
        # Sample Reliability Tier
        if total_balls >= 150:
            confidence_tier = 'High Confidence'
        elif total_balls >= 60:
            confidence_tier = 'Moderate Confidence'
        else:
            confidence_tier = 'Low Confidence (Small Sample)'
            
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'matches_played': matches,
            'total_deliveries_faced': total_balls,
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ball_ratio': round(p_balls / total_balls, 3),
            'actual_runs': actual_runs,
            'expected_runs': round(exp_runs, 1),
            'raw_run_residual': round(raw_run_delta, 2),
            'shrunk_run_residual': round(shrunk_total_run_delta, 2),
            'run_residual_per_100_balls': round(100.0 * (raw_run_delta / total_balls), 2),
            'shrunk_run_residual_per_100_balls': round(100.0 * shrunk_run_delta_per_ball, 2),
            'pressure_adjusted_run_delta': round(pressure_adj_run_delta, 2),
            'pressure_run_residual': round(p_run_delta, 2),
            'nonpressure_run_residual': round(np_run_delta, 2),
            'pressure_run_residual_per_100': round(100.0 * (p_run_delta / p_balls), 2) if p_balls > 0 else 0.0,
            'actual_dismissals': actual_outs,
            'expected_dismissals': round(exp_outs, 1),
            'dismissal_residual': round(out_delta, 2),
            'confidence_tier': confidence_tier
        })
        
    res_df = pd.DataFrame(records)
    return res_df.sort_values(['competition_scope', 'shrunk_run_residual'], ascending=[True, False]).reset_index(drop=True)

def aggregate_bowler_performance(df: pd.DataFrame, m_prior: float = 30.0) -> pd.DataFrame:
    '''
    Aggregates delivery-level bowling residuals to player level.
    Applies empirical Bayes shrinkage towards context neutral mean (0.0).
    m_prior: pseudo-sample weight for shrinkage (30 balls).
    '''
    d = df.copy()
    d['is_pressure'] = d['pressure_score'].ge(50.0)
    
    records = []
    for (pid, pname, scope), grp in d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope']):
        total_balls = len(grp)
        actual_runs = grp['actual_runs_conceded'].sum()
        exp_runs = grp['expected_runs_conceded'].sum()
        raw_run_delta = grp['bowling_run_residual'].sum()
        pressure_adj_run_delta = grp['pressure_adjusted_bowling_run_delta'].sum()
        
        actual_wkts = grp['actual_wicket_outcome'].sum()
        exp_wkts = grp['expected_wicket_prob'].sum()
        wkt_delta = grp['bowling_wicket_residual'].sum()
        pressure_adj_wkt_delta = grp['pressure_adjusted_bowling_wicket_delta'].sum()
        
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        p_run_delta = p_grp['bowling_run_residual'].sum() if p_balls > 0 else 0.0
        p_adj_run_delta = p_grp['pressure_adjusted_bowling_run_delta'].sum() if p_balls > 0 else 0.0
        p_wkt_delta = p_grp['bowling_wicket_residual'].sum() if p_balls > 0 else 0.0
        
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        np_run_delta = np_grp['bowling_run_residual'].sum() if np_balls > 0 else 0.0
        
        matches = grp['match_id'].nunique()
        
        # Bayesian Shrinkage on run residual per ball
        shrinkage_weight = total_balls / (total_balls + m_prior)
        mean_run_delta_per_ball = raw_run_delta / total_balls
        shrunk_run_delta_per_ball = mean_run_delta_per_ball * shrinkage_weight
        shrunk_total_run_delta = shrunk_run_delta_per_ball * total_balls
        
        # Confidence Tier
        if total_balls >= 150:
            confidence_tier = 'High Confidence'
        elif total_balls >= 60:
            confidence_tier = 'Moderate Confidence'
        else:
            confidence_tier = 'Low Confidence (Small Sample)'
            
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'matches_played': matches,
            'total_deliveries_bowled': total_balls,
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ball_ratio': round(p_balls / total_balls, 3),
            'actual_runs_conceded': actual_runs,
            'expected_runs_conceded': round(exp_runs, 1),
            'raw_run_residual': round(raw_run_delta, 2),
            'shrunk_run_residual': round(shrunk_total_run_delta, 2),
            'run_residual_per_100_balls': round(100.0 * (raw_run_delta / total_balls), 2),
            'shrunk_run_residual_per_100_balls': round(100.0 * shrunk_run_delta_per_ball, 2),
            'pressure_adjusted_run_delta': round(pressure_adj_run_delta, 2),
            'pressure_run_residual': round(p_run_delta, 2),
            'nonpressure_run_residual': round(np_run_delta, 2),
            'pressure_run_residual_per_100': round(100.0 * (p_run_delta / p_balls), 2) if p_balls > 0 else 0.0,
            'actual_credited_wickets': actual_wkts,
            'expected_wickets': round(exp_wkts, 1),
            'wicket_residual': round(wkt_delta, 2),
            'pressure_adjusted_wicket_delta': round(pressure_adj_wkt_delta, 2),
            'confidence_tier': confidence_tier
        })
        
    res_df = pd.DataFrame(records)
    return res_df.sort_values(['competition_scope', 'shrunk_run_residual'], ascending=[True, False]).reset_index(drop=True)
