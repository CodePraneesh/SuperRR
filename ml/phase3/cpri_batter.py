# cpri_batter.py
# Phase 3: Batter CPRI (Clutch Performance & Reliability Index) Engine.
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase3.reliability import (
    apply_bayesian_shrinkage,
    calculate_reliability_confidence,
    assign_confidence_tier,
    min_max_normalize
)

def compute_batter_cpri(
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
    if 'batting_wpa' not in d.columns:
        w_cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'batting_wpa']
        d = d.merge(wpa_df[w_cols], on=['match_id', 'innings', 'overid', 'over_ball_num'], how='left')
        d['batting_wpa'] = d['batting_wpa'].fillna(0.0)
        
    d['is_pressure'] = d['pressure_score'].ge(50.0)
    
    # 1. Match-level aggregates for consistency
    match_grp = d.groupby(['striker_id', 'striker_name_clean', 'competition_scope', 'match_id']).agg(
        match_balls=('actual_batter_runs', 'count'),
        match_pressure_balls=('is_pressure', 'sum'),
        match_run_delta=('pressure_adjusted_batting_run_delta', 'sum'),
        match_out_delta=('pressure_adjusted_batting_out_delta', 'sum'),
        match_wpa=('batting_wpa', 'sum')
    ).reset_index()
    
    # Match net impact per 100 balls
    match_grp['match_net_impact_rate'] = (
        (match_grp['match_run_delta'] - 12.0 * match_grp['match_out_delta']) / 
        np.maximum(1, match_grp['match_balls'])
    ) * 100.0
    
    # Consistency by player & scope: proportion of matches with positive rate, and inverse std
    consistency_df = match_grp.groupby(['striker_id', 'competition_scope']).agg(
        matches_played=('match_id', 'nunique'),
        positive_match_ratio=('match_net_impact_rate', lambda s: float((s > 0).mean())),
        impact_rate_std=('match_net_impact_rate', lambda s: float(s.std(ddof=0)) if len(s) > 1 else 15.0)
    ).reset_index().rename(columns={'striker_id': 'player_id'})
    
    # Lower std and higher positive match ratio means more consistent clutch performance
    consistency_df['raw_consistency'] = (
        consistency_df['positive_match_ratio'] * 70.0 + 
        np.clip(100.0 - consistency_df['impact_rate_std'], 0.0, 100.0) * 0.30
    )
    
    # 2. Player-level aggregates
    records = []
    for (pid, pname, scope), grp in d.groupby(['striker_id', 'striker_name_clean', 'competition_scope']):
        total_balls = len(grp)
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        # Pressure Impact metrics
        tot_run_delta = grp['pressure_adjusted_batting_run_delta'].sum()
        tot_out_delta = grp['pressure_adjusted_batting_out_delta'].sum()
        tot_wpa = grp['batting_wpa'].sum()
        
        # Net residual runs above expected per 100 balls in pressure
        # Out delta: positive = survived risk; negative = lost wicket
        # Credit runs plus survival value (1 dismissal ≈ 12 runs in T20)
        p_run_res = p_grp['batting_run_residual'].sum() if p_balls > 0 else 0.0
        p_out_res = p_grp['batting_dismissal_residual'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['batting_wpa'].sum() if p_balls > 0 else 0.0
        
        # Pressure Impact composite: 60% expected run/dismissal residual rate + 40% WPA rate
        p_rate_runs = (p_run_res / max(1, p_balls)) * 100.0
        p_rate_outs = (p_out_res / max(1, p_balls)) * 100.0
        p_rate_wpa = (p_wpa / max(1, p_balls)) * 100.0
        
        # Raw pressure impact rate
        raw_pressure_impact = (p_rate_runs - 12.0 * p_rate_outs) + 25.0 * p_rate_wpa
        
        # Adaptability: differential between pressure and non-pressure performance
        np_run_res = np_grp['batting_run_residual'].sum() if np_balls > 0 else 0.0
        np_out_res = np_grp['batting_dismissal_residual'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['batting_wpa'].sum() if np_balls > 0 else 0.0
        
        np_rate_runs = (np_run_res / max(1, np_balls)) * 100.0
        np_rate_outs = (np_out_res / max(1, np_balls)) * 100.0
        np_rate_wpa = (np_wpa / max(1, np_balls)) * 100.0
        raw_np_impact = (np_rate_runs - 12.0 * np_rate_outs) + 25.0 * np_rate_wpa
        
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
            'actual_runs': grp['actual_batter_runs'].sum(),
            'expected_runs': round(grp['expected_batter_runs'].sum(), 2)
        })
        
    summary = pd.DataFrame(records)
    summary = summary.merge(consistency_df, on=['player_id', 'competition_scope'], how='left')
    
    # 3. Apply Empirical Bayes Shrinkage and Normalization per Competition Scope
    scoped_summaries = []
    for scope, grp in summary.groupby('competition_scope'):
        g = grp.copy()
        
        # Bayesian shrinkage on pressure impact and adaptability
        g['shrunk_pressure_impact'] = apply_bayesian_shrinkage(
            g['raw_pressure_impact'], g['pressure_deliveries'], m_prior_weight=40.0
        )
        g['shrunk_adaptability'] = apply_bayesian_shrinkage(
            g['raw_adaptability'], np.minimum(g['pressure_deliveries'], g['nonpressure_deliveries']), m_prior_weight=40.0
        )
        g['shrunk_consistency'] = apply_bayesian_shrinkage(
            g['raw_consistency'], g['matches_played'], m_prior_weight=5.0
        )
        
        # Normalize 4 dimensions onto [0, 100] scale
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        g['score_adaptability'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_reliability_confidence(g['total_deliveries'], n_threshold=150.0)
        
        # Composite CPRI
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
        
    all_batters = pd.concat(scoped_summaries, ignore_index=True)
    return all_batters, match_grp
