# ml/phase3_3/cpri_unified.py
# Phase 3.3: Unified CPRI Computation Engine for Batters and Bowlers.
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase3_2.reliability import (
    apply_bayesian_shrinkage,
    calculate_pressure_reliability,
    min_max_normalize,
    robust_sigmoid_normalize
)
from ml.phase3_3.confidence_system import (
    calculate_effective_sample_size,
    calculate_pressure_uncertainty,
    assess_nonpressure_adequacy,
    assign_batter_confidence_tier_33,
    assign_bowler_confidence_tier_33
)

WEIGHTS = {
    'pressure_impact': 0.40,
    'adaptability': 0.25,
    'consistency': 0.20,
    'reliability': 0.15
}

def compute_unified_batter_cpri(
    deliveries_df: pd.DataFrame,
    wpa_df: pd.DataFrame,
    wicket_value: float = 12.0,
    wpa_multiplier: float = 25.0,
    pressure_threshold: float = 50.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Phase 3.3 Unified Batter CPRI rankings.
    """
    d = deliveries_df.copy()
    if 'batting_wpa' not in d.columns:
        w_cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'batting_wpa']
        d = d.merge(wpa_df[w_cols], on=['match_id', 'innings', 'overid', 'over_ball_num'], how='left')
        d['batting_wpa'] = d['batting_wpa'].fillna(0.0)
        
    d['is_pressure'] = d['pressure_score'].ge(pressure_threshold)
    d['delivery_survival_contribution'] = d['batting_dismissal_residual']
    d['delivery_net_impact'] = (
        d['batting_run_residual'] + 
        wicket_value * d['delivery_survival_contribution'] + 
        wpa_multiplier * d['batting_wpa']
    )
    
    # Match-level aggregates in pressure
    p_delivs = d[d['is_pressure']].copy()
    p_match_grp = p_delivs.groupby(['striker_id', 'striker_name_clean', 'competition_scope', 'match_id']).agg(
        match_pressure_balls=('actual_batter_runs', 'count'),
        match_run_res=('batting_run_residual', 'sum'),
        match_surv_res=('delivery_survival_contribution', 'sum'),
        match_wpa=('batting_wpa', 'sum'),
        match_net_impact=('delivery_net_impact', 'sum')
    ).reset_index()
    
    p_match_grp['match_impact_rate'] = (p_match_grp['match_net_impact'] / p_match_grp['match_pressure_balls']) * 100.0
    
    consistency_df = p_match_grp.groupby(['striker_id', 'competition_scope']).agg(
        pressure_matches=('match_id', 'nunique'),
        pos_pressure_match_ratio=('match_net_impact', lambda s: float((s > 0).mean())),
        mean_match_residual=('match_impact_rate', lambda s: float(s.mean())),
        std_match_residual=('match_impact_rate', lambda s: float(s.std(ddof=0)) if len(s) > 1 else 15.0)
    ).reset_index().rename(columns={'striker_id': 'player_id'})
    
    consistency_df['raw_consistency'] = (
        consistency_df['pos_pressure_match_ratio'] * 50.0 +
        np.clip(50.0 + consistency_df['mean_match_residual'] * 0.20, 0.0, 100.0) * 0.30 +
        np.clip(100.0 - consistency_df['std_match_residual'] * 0.50, 0.0, 100.0) * 0.20
    )
    
    records = []
    for (pid, pname, scope), grp in d.groupby(['striker_id', 'striker_name_clean', 'competition_scope']):
        tot_balls = len(grp)
        tot_matches = grp['match_id'].nunique()
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        # Pressure Impact
        p_run = p_grp['batting_run_residual'].sum() if p_balls > 0 else 0.0
        p_surv = p_grp['delivery_survival_contribution'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['batting_wpa'].sum() if p_balls > 0 else 0.0
        
        raw_p_impact = (p_run / max(1, p_balls))*100.0 + wicket_value*(p_surv / max(1, p_balls))*100.0 + wpa_multiplier*(p_wpa / max(1, p_balls))*100.0
        
        # Non-pressure Impact
        np_run = np_grp['batting_run_residual'].sum() if np_balls > 0 else 0.0
        np_surv = np_grp['delivery_survival_contribution'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['batting_wpa'].sum() if np_balls > 0 else 0.0
        
        raw_np_impact = (np_run / max(1, np_balls))*100.0 + wicket_value*(np_surv / max(1, np_balls))*100.0 + wpa_multiplier*(np_wpa / max(1, np_balls))*100.0
        raw_adapt = raw_p_impact - raw_np_impact
        
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'role': 'Batter',
            'total_deliveries': tot_balls,
            'total_matches': tot_matches,
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ratio': round(p_balls / tot_balls, 4),
            'raw_pressure_impact': raw_p_impact,
            'raw_nonpressure_impact': raw_np_impact,
            'raw_adaptability': raw_adapt,
            'total_wpa': round(grp['batting_wpa'].sum(), 4),
            'pressure_wpa': round(p_wpa, 4),
            'actual_runs': grp['actual_batter_runs'].sum(),
            'expected_runs': round(grp['expected_batter_runs'].sum(), 2),
            'actual_dismissals': int((grp['actual_dismissal_outcome'] == 1).sum()),
            'expected_dismissals': round(grp['expected_dismissal_prob'].sum(), 2),
            'actual_runs_in_pressure': p_grp['actual_batter_runs'].sum() if p_balls > 0 else 0,
            'expected_runs_in_pressure': round(p_grp['expected_batter_runs'].sum(), 2) if p_balls > 0 else 0.0,
            'actual_dismissals_in_pressure': int((p_grp['actual_dismissal_outcome'] == 1).sum()) if p_balls > 0 else 0,
            'expected_dismissals_in_pressure': round(p_grp['expected_dismissal_prob'].sum(), 2) if p_balls > 0 else 0.0
        })
        
    summary = pd.DataFrame(records)
    summary = summary.merge(consistency_df, on=['player_id', 'competition_scope'], how='left')
    summary['pressure_matches'] = summary['pressure_matches'].fillna(0).astype(int)
    summary['raw_consistency'] = summary['raw_consistency'].fillna(30.0)
    summary['pos_pressure_match_ratio'] = summary['pos_pressure_match_ratio'].fillna(0.0)
    summary['mean_match_residual'] = summary['mean_match_residual'].fillna(0.0)
    summary['std_match_residual'] = summary['std_match_residual'].fillna(15.0)
    
    # Statistical reliability & sample size diagnostics
    summary['effective_pressure_sample_size'] = calculate_effective_sample_size(summary['pressure_deliveries'], summary['pressure_matches'])
    summary['pressure_specific_uncertainty'] = calculate_pressure_uncertainty(summary['std_match_residual'], summary['pressure_matches'])
    summary['nonpressure_sample_adequacy'] = assess_nonpressure_adequacy(summary['nonpressure_deliveries'], threshold=60.0)
    
    scoped = []
    for scope, grp in summary.groupby('competition_scope'):
        g = grp.copy()
        g['shrunk_pressure_impact'] = apply_bayesian_shrinkage(g['raw_pressure_impact'], g['pressure_deliveries'], m_prior_weight=40.0)
        g['shrunk_adaptability'] = apply_bayesian_shrinkage(g['raw_adaptability'], np.minimum(g['pressure_deliveries'], g['nonpressure_deliveries']), m_prior_weight=40.0)
        g['shrunk_consistency'] = apply_bayesian_shrinkage(g['raw_consistency'], g['pressure_matches'], m_prior_weight=5.0)
        
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        g['score_adaptability'] = robust_sigmoid_normalize(g['shrunk_adaptability'], k=0.6)
        g['score_adaptability_p31_minmax'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_pressure_reliability(g['pressure_deliveries'], g['pressure_matches'])
        
        # Composite CPRI
        g['cpri_score'] = (
            WEIGHTS['pressure_impact'] * g['score_pressure_impact'] +
            WEIGHTS['adaptability'] * g['score_adaptability'] +
            WEIGHTS['consistency'] * g['score_consistency'] +
            WEIGHTS['reliability'] * g['score_reliability']
        ).round(2)
        
        g['confidence_tier'] = assign_batter_confidence_tier_33(
            g['total_deliveries'], g['pressure_deliveries'], g['pressure_matches'], g['nonpressure_deliveries']
        )
        g = g.sort_values('cpri_score', ascending=False).reset_index(drop=True)
        g['rank'] = g.index + 1
        scoped.append(g)
        
    return pd.concat(scoped, ignore_index=True), p_match_grp

def compute_unified_bowler_cpri(
    deliveries_df: pd.DataFrame,
    wpa_df: pd.DataFrame,
    wicket_value: float = 12.0,
    wpa_multiplier: float = 25.0,
    pressure_threshold: float = 50.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Phase 3.3 Unified Bowler CPRI rankings.
    """
    d = deliveries_df.copy()
    if 'bowling_wpa' not in d.columns:
        w_cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'bowling_wpa']
        d = d.merge(wpa_df[w_cols], on=['match_id', 'innings', 'overid', 'over_ball_num'], how='left')
        d['bowling_wpa'] = d['bowling_wpa'].fillna(0.0)
        
    d['is_pressure'] = d['pressure_score'].ge(pressure_threshold)
    d['delivery_net_impact'] = (
        d['bowling_run_residual'] + 
        wicket_value * d['bowling_wicket_residual'] + 
        wpa_multiplier * d['bowling_wpa']
    )
    
    # Match-level aggregates in pressure
    p_delivs = d[d['is_pressure']].copy()
    p_match_grp = p_delivs.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope', 'match_id']).agg(
        match_pressure_balls=('actual_runs_conceded', 'count'),
        match_run_res=('bowling_run_residual', 'sum'),
        match_wkt_res=('bowling_wicket_residual', 'sum'),
        match_wpa=('bowling_wpa', 'sum'),
        match_net_impact=('delivery_net_impact', 'sum')
    ).reset_index()
    
    p_match_grp['match_impact_rate'] = (p_match_grp['match_net_impact'] / p_match_grp['match_pressure_balls']) * 100.0
    
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
    
    records = []
    for (pid, pname, scope), grp in d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope']):
        tot_balls = len(grp)
        tot_matches = grp['match_id'].nunique()
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        # Pressure Impact
        p_run = p_grp['bowling_run_residual'].sum() if p_balls > 0 else 0.0
        p_wkt = p_grp['bowling_wicket_residual'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['bowling_wpa'].sum() if p_balls > 0 else 0.0
        
        raw_p_impact = (p_run / max(1, p_balls))*100.0 + wicket_value*(p_wkt / max(1, p_balls))*100.0 + wpa_multiplier*(p_wpa / max(1, p_balls))*100.0
        
        # Non-pressure Impact
        np_run = np_grp['bowling_run_residual'].sum() if np_balls > 0 else 0.0
        np_wkt = np_grp['bowling_wicket_residual'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['bowling_wpa'].sum() if np_balls > 0 else 0.0
        
        raw_np_impact = (np_run / max(1, np_balls))*100.0 + wicket_value*(np_wkt / max(1, np_balls))*100.0 + wpa_multiplier*(np_wpa / max(1, np_balls))*100.0
        raw_adapt = raw_p_impact - raw_np_impact
        
        records.append({
            'player_id': pid,
            'player_name': pname,
            'competition_scope': scope,
            'role': 'Bowler',
            'total_deliveries': tot_balls,
            'total_matches': tot_matches,
            'balls_per_match': round(tot_balls / tot_matches, 2),
            'pressure_deliveries': p_balls,
            'nonpressure_deliveries': np_balls,
            'pressure_ratio': round(p_balls / tot_balls, 4),
            'raw_pressure_impact': raw_p_impact,
            'raw_nonpressure_impact': raw_np_impact,
            'raw_adaptability': raw_adapt,
            'total_wpa': round(grp['bowling_wpa'].sum(), 4),
            'pressure_wpa': round(p_wpa, 4),
            'actual_runs_conceded': grp['actual_runs_conceded'].sum(),
            'expected_runs_conceded': round(grp['expected_runs_conceded'].sum(), 2),
            'actual_credited_wickets': int(grp['actual_wicket_outcome'].sum()),
            'expected_wickets': round(grp['expected_wicket_prob'].sum(), 2),
            'actual_runs_conceded_in_pressure': p_grp['actual_runs_conceded'].sum() if p_balls > 0 else 0,
            'expected_runs_conceded_in_pressure': round(p_grp['expected_runs_conceded'].sum(), 2) if p_balls > 0 else 0.0,
            'actual_credited_wickets_in_pressure': int(p_grp['actual_wicket_outcome'].sum()) if p_balls > 0 else 0,
            'expected_wickets_in_pressure': round(p_grp['expected_wicket_prob'].sum(), 2) if p_balls > 0 else 0.0
        })
        
    summary = pd.DataFrame(records)
    summary = summary.merge(consistency_df, on=['player_id', 'competition_scope'], how='left')
    summary['pressure_matches'] = summary['pressure_matches'].fillna(0).astype(int)
    summary['raw_consistency'] = summary['raw_consistency'].fillna(30.0)
    summary['pos_pressure_match_ratio'] = summary['pos_pressure_match_ratio'].fillna(0.0)
    summary['mean_match_residual'] = summary['mean_match_residual'].fillna(0.0)
    summary['std_match_residual'] = summary['std_match_residual'].fillna(15.0)
    
    # Statistical reliability & sample size diagnostics
    summary['effective_pressure_sample_size'] = calculate_effective_sample_size(summary['pressure_deliveries'], summary['pressure_matches'])
    summary['pressure_specific_uncertainty'] = calculate_pressure_uncertainty(summary['std_match_residual'], summary['pressure_matches'])
    summary['nonpressure_sample_adequacy'] = assess_nonpressure_adequacy(summary['nonpressure_deliveries'], threshold=60.0)
    
    scoped = []
    for scope, grp in summary.groupby('competition_scope'):
        g = grp.copy()
        g['shrunk_pressure_impact'] = apply_bayesian_shrinkage(g['raw_pressure_impact'], g['pressure_deliveries'], m_prior_weight=40.0)
        g['shrunk_adaptability'] = apply_bayesian_shrinkage(g['raw_adaptability'], np.minimum(g['pressure_deliveries'], g['nonpressure_deliveries']), m_prior_weight=40.0)
        g['shrunk_consistency'] = apply_bayesian_shrinkage(g['raw_consistency'], g['pressure_matches'], m_prior_weight=5.0)
        
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        g['score_adaptability'] = robust_sigmoid_normalize(g['shrunk_adaptability'], k=0.6)
        g['score_adaptability_p31_minmax'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_pressure_reliability(g['pressure_deliveries'], g['pressure_matches'])
        
        # Composite CPRI
        g['cpri_score'] = (
            WEIGHTS['pressure_impact'] * g['score_pressure_impact'] +
            WEIGHTS['adaptability'] * g['score_adaptability'] +
            WEIGHTS['consistency'] * g['score_consistency'] +
            WEIGHTS['reliability'] * g['score_reliability']
        ).round(2)
        
        g['confidence_tier'] = assign_bowler_confidence_tier_33(
            g['total_deliveries'], g['pressure_deliveries'], g['pressure_matches'], g['balls_per_match']
        )
        g = g.sort_values('cpri_score', ascending=False).reset_index(drop=True)
        g['rank'] = g.index + 1
        scoped.append(g)
        
    return pd.concat(scoped, ignore_index=True), p_match_grp
