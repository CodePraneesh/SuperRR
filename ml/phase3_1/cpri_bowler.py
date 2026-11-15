# ml/phase3_1/cpri_bowler.py
# Phase 3.1: Bowler CPRI Engine with Pressure-Specific Reliability & Player Consistency.
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase3_1.reliability import (
    apply_bayesian_shrinkage,
    calculate_pressure_reliability,
    assign_pressure_confidence_tier,
    min_max_normalize
)

def compute_bowler_cpri_31(
    deliveries_df: pd.DataFrame,
    wpa_df: pd.DataFrame,
    weights: dict[str, float] = None,
    wicket_value: float = 12.0,
    wpa_multiplier: float = 25.0,
    pressure_threshold: float = 50.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Phase 3.1 Bowler CPRI rankings.
    Key methodology features:
    1. Legal Credited Wickets:
       bowling_wicket_residual = (actual_credited_wicket - expected_wicket_prob).
       Wicket contribution = +wicket_value * bowling_wicket_residual.
    2. Player-Specific Clutch Consistency:
       Evaluated on matches containing pressure deliveries.
       Combines % of positive pressure matches, mean match residual, and inverse match std.
    3. Pressure-Specific Reliability:
       Joint function of pressure deliveries and pressure matches.
    """
    if weights is None:
        weights = {
            'pressure_impact': 0.40,
            'adaptability': 0.25,
            'consistency': 0.20,
            'reliability': 0.15
        }
        
    d = deliveries_df.copy()
    if 'bowling_wpa' not in d.columns:
        w_cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'bowling_wpa']
        d = d.merge(wpa_df[w_cols], on=['match_id', 'innings', 'overid', 'over_ball_num'], how='left')
        d['bowling_wpa'] = d['bowling_wpa'].fillna(0.0)
        
    d['is_pressure'] = d['pressure_score'].ge(pressure_threshold)
    
    # Delivery net impact:
    # bowling_run_residual = expected - actual (runs saved)
    # bowling_wicket_residual = actual credited wicket - expected prob (wickets above expected)
    d['delivery_net_impact'] = (
        d['bowling_run_residual'] + 
        wicket_value * d['bowling_wicket_residual'] + 
        wpa_multiplier * d['bowling_wpa']
    )
    
    # 1. Match-level aggregates (filtered to matches where bowler bowled in pressure)
    p_delivs = d[d['is_pressure']].copy()
    p_match_grp = p_delivs.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope', 'match_id']).agg(
        match_pressure_balls=('actual_runs_conceded', 'count'),
        match_run_res=('bowling_run_residual', 'sum'),
        match_wkt_res=('bowling_wicket_residual', 'sum'),
        match_wpa=('bowling_wpa', 'sum'),
        match_net_impact=('delivery_net_impact', 'sum')
    ).reset_index()
    
    p_match_grp['match_impact_rate'] = (
        p_match_grp['match_net_impact'] / p_match_grp['match_pressure_balls']
    ) * 100.0
    
    consistency_df = p_match_grp.groupby(['bowler_id', 'competition_scope']).agg(
        pressure_matches=('match_id', 'nunique'),
        pos_pressure_match_ratio=('match_net_impact', lambda s: float((s > 0).mean())),
        mean_match_residual=('match_impact_rate', lambda s: float(s.mean())),
        std_match_residual=('match_impact_rate', lambda s: float(s.std(ddof=0)) if len(s) > 1 else 15.0)
    ).reset_index().rename(columns={'bowler_id': 'player_id'})
    
    consistency_df['raw_consistency'] = (
        consistency_df['pos_pressure_match_ratio'] * 50.0 +
        np.clip(50.0 + consistency_df['mean_match_residual'] * 0.20, 0.0, 100.0) * 0.30 +
        np.clip(100.0 - consistency_df['std_match_residual'] * 0.50, 0.0, 100.0) * 0.20
    )
    
    # 2. Player-level aggregates
    records = []
    for (pid, pname, scope), grp in d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope']):
        total_balls = len(grp)
        total_matches = grp['match_id'].nunique()
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        # Pressure residuals
        p_run_res = p_grp['bowling_run_residual'].sum() if p_balls > 0 else 0.0
        p_wkt_res = p_grp['bowling_wicket_residual'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['bowling_wpa'].sum() if p_balls > 0 else 0.0
        
        p_rate_runs = (p_run_res / max(1, p_balls)) * 100.0
        p_rate_wkts = (p_wkt_res / max(1, p_balls)) * 100.0
        p_rate_wpa = (p_wpa / max(1, p_balls)) * 100.0
        
        raw_pressure_impact = p_rate_runs + wicket_value * p_rate_wkts + wpa_multiplier * p_rate_wpa
        
        # Adaptability
        np_run_res = np_grp['bowling_run_residual'].sum() if np_balls > 0 else 0.0
        np_wkt_res = np_grp['bowling_wicket_residual'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['bowling_wpa'].sum() if np_balls > 0 else 0.0
        
        np_rate_runs = (np_run_res / max(1, np_balls)) * 100.0
        np_rate_wkts = (np_wkt_res / max(1, np_balls)) * 100.0
        np_rate_wpa = (np_wpa / max(1, np_balls)) * 100.0
        raw_np_impact = np_rate_runs + wicket_value * np_rate_wkts + wpa_multiplier * np_rate_wpa
        
        raw_adaptability = raw_pressure_impact - raw_np_impact
        
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'total_deliveries': total_balls,
            'total_matches': total_matches,
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ratio': round(p_balls / total_balls, 4),
            'raw_pressure_impact': raw_pressure_impact,
            'raw_adaptability': raw_adaptability,
            'total_wpa': round(grp['bowling_wpa'].sum(), 4),
            'pressure_wpa': round(p_wpa, 4),
            'actual_runs_conceded': grp['actual_runs_conceded'].sum(),
            'expected_runs_conceded': round(grp['expected_runs_conceded'].sum(), 2),
            'actual_credited_wickets': int(grp['actual_wicket_outcome'].sum()),
            'expected_wickets': round(grp['expected_wicket_prob'].sum(), 2)
        })
        
    summary = pd.DataFrame(records)
    summary = summary.merge(consistency_df, on=['player_id', 'competition_scope'], how='left')
    summary['pressure_matches'] = summary['pressure_matches'].fillna(0).astype(int)
    summary['raw_consistency'] = summary['raw_consistency'].fillna(30.0)
    
    # 3. Apply Empirical Bayes Shrinkage and Normalization per Competition Scope
    scoped_summaries = []
    for scope, grp in summary.groupby('competition_scope'):
        g = grp.copy()
        
        g['shrunk_pressure_impact'] = apply_bayesian_shrinkage(
            g['raw_pressure_impact'], g['pressure_deliveries'], m_prior_weight=40.0
        )
        g['shrunk_adaptability'] = apply_bayesian_shrinkage(
            g['raw_adaptability'], np.minimum(g['pressure_deliveries'], g['nonpressure_deliveries']), m_prior_weight=40.0
        )
        g['shrunk_consistency'] = apply_bayesian_shrinkage(
            g['raw_consistency'], g['pressure_matches'], m_prior_weight=5.0
        )
        
        # Normalized Component Scores [0, 100]
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        g['score_adaptability'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_pressure_reliability(g['pressure_deliveries'], g['pressure_matches'])
        
        # Composite CPRI
        g['cpri_score'] = (
            weights['pressure_impact'] * g['score_pressure_impact'] +
            weights['adaptability'] * g['score_adaptability'] +
            weights['consistency'] * g['score_consistency'] +
            weights['reliability'] * g['score_reliability']
        ).round(2)
        
        g['confidence_tier'] = assign_pressure_confidence_tier(
            g['total_deliveries'], g['pressure_deliveries'], g['pressure_matches']
        )
        g = g.sort_values('cpri_score', ascending=False).reset_index(drop=True)
        g['rank'] = g.index + 1
        scoped_summaries.append(g)
        
    all_bowlers = pd.concat(scoped_summaries, ignore_index=True)
    return all_bowlers, p_match_grp
