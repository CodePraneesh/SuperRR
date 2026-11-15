# cpri_bowler.py
# Phase 3: Bowler CPRI (Clutch Performance & Reliability Index) Engine.
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase3.reliability import (
    apply_bayesian_shrinkage,
    calculate_reliability_confidence,
    assign_confidence_tier,
    min_max_normalize
)

def compute_bowler_cpri(
    deliveries_df: pd.DataFrame,
    wpa_df: pd.DataFrame,
    weights: dict[str, float] = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
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
        
    d['is_pressure'] = d['pressure_score'].ge(50.0)
    
    # 1. Match-level aggregates for consistency
    match_grp = d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope', 'match_id']).agg(
        match_balls=('actual_runs_conceded', 'count'),
        match_pressure_balls=('is_pressure', 'sum'),
        match_run_delta=('pressure_adjusted_bowling_run_delta', 'sum'),
        match_wkt_delta=('pressure_adjusted_bowling_wicket_delta', 'sum'),
        match_wpa=('bowling_wpa', 'sum')
    ).reset_index()
    
    # Match net impact per 100 balls: runs saved + wicket bonus (1 wicket ≈ 12 runs saved in T20)
    match_grp['match_net_impact_rate'] = (
        (match_grp['match_run_delta'] + 12.0 * match_grp['match_wkt_delta']) / 
        np.maximum(1, match_grp['match_balls'])
    ) * 100.0
    
    consistency_df = match_grp.groupby(['bowler_id', 'competition_scope']).agg(
        matches_played=('match_id', 'nunique'),
        positive_match_ratio=('match_net_impact_rate', lambda s: float((s > 0).mean())),
        impact_rate_std=('match_net_impact_rate', lambda s: float(s.std(ddof=0)) if len(s) > 1 else 15.0)
    ).reset_index().rename(columns={'bowler_id': 'player_id'})
    
    consistency_df['raw_consistency'] = (
        consistency_df['positive_match_ratio'] * 70.0 + 
        np.clip(100.0 - consistency_df['impact_rate_std'], 0.0, 100.0) * 0.30
    )
    
    # 2. Player-level aggregates
    records = []
    for (pid, pname, scope), grp in d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope']):
        total_balls = len(grp)
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        tot_run_delta = grp['pressure_adjusted_bowling_run_delta'].sum()
        tot_wkt_delta = grp['pressure_adjusted_bowling_wicket_delta'].sum()
        tot_wpa = grp['bowling_wpa'].sum()
        
        # Pressure residuals:
        # bowling_run_residual: positive = saved runs relative to expected
        # bowling_wicket_residual: positive = took more credited wickets than expected
        p_run_res = p_grp['bowling_run_residual'].sum() if p_balls > 0 else 0.0
        p_wkt_res = p_grp['bowling_wicket_residual'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['bowling_wpa'].sum() if p_balls > 0 else 0.0
        
        p_rate_runs = (p_run_res / max(1, p_balls)) * 100.0
        p_rate_wkts = (p_wkt_res / max(1, p_balls)) * 100.0
        p_rate_wpa = (p_wpa / max(1, p_balls)) * 100.0
        
        # Raw pressure impact rate
        raw_pressure_impact = (p_rate_runs + 12.0 * p_rate_wkts) + 25.0 * p_rate_wpa
        
        # Adaptability: differential between pressure and non-pressure bowling performance
        np_run_res = np_grp['bowling_run_residual'].sum() if np_balls > 0 else 0.0
        np_wkt_res = np_grp['bowling_wicket_residual'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['bowling_wpa'].sum() if np_balls > 0 else 0.0
        
        np_rate_runs = (np_run_res / max(1, np_balls)) * 100.0
        np_rate_wkts = (np_wkt_res / max(1, np_balls)) * 100.0
        np_rate_wpa = (np_wpa / max(1, np_balls)) * 100.0
        raw_np_impact = (np_rate_runs + 12.0 * np_rate_wkts) + 25.0 * np_rate_wpa
        
        raw_adaptability = raw_pressure_impact - raw_np_impact
        
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'total_deliveries': total_balls,
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ratio': round(p_balls / total_balls, 4),
            'raw_pressure_impact': raw_pressure_impact,
            'raw_adaptability': raw_adaptability,
            'total_wpa': round(tot_wpa, 4),
            'pressure_wpa': round(p_wpa, 4),
            'actual_runs_conceded': grp['actual_runs_conceded'].sum(),
            'expected_runs_conceded': round(grp['expected_runs_conceded'].sum(), 2),
            'actual_credited_wickets': int(grp['actual_wicket_outcome'].sum())
        })
        
    summary = pd.DataFrame(records)
    summary = summary.merge(consistency_df, on=['player_id', 'competition_scope'], how='left')
    
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
            g['raw_consistency'], g['matches_played'], m_prior_weight=5.0
        )
        
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        g['score_adaptability'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_reliability_confidence(g['total_deliveries'], n_threshold=150.0)
        
        g['cpri_score'] = (
            weights['pressure_impact'] * g['score_pressure_impact'] +
            weights['adaptability'] * g['score_adaptability'] +
            weights['consistency'] * g['score_consistency'] +
            weights['reliability'] * g['score_reliability']
        ).round(2)
        
        g['confidence_tier'] = assign_confidence_tier(g['total_deliveries'], high_thresh=150, mod_thresh=60)
        g = g.sort_values('cpri_score', ascending=False).reset_index(drop=True)
        g['rank'] = g.index + 1
        scoped_summaries.append(g)
        
    all_bowlers = pd.concat(scoped_summaries, ignore_index=True)
    return all_bowlers, match_grp
