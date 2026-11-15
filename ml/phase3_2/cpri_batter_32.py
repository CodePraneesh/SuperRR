# ml/phase3_2/cpri_batter_32.py
# Phase 3.2: Batter CPRI Engine with Robust Adaptability Scaling & Strict Sample Eligibility.
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase3_2.reliability import (
    apply_bayesian_shrinkage,
    calculate_pressure_reliability,
    min_max_normalize,
    robust_sigmoid_normalize,
    assign_batter_eligibility_tier
)

def compute_batter_cpri_32(
    deliveries_df: pd.DataFrame,
    wpa_df: pd.DataFrame,
    weights: dict[str, float] = None,
    wicket_value: float = 12.0,
    wpa_multiplier: float = 25.0,
    pressure_threshold: float = 50.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Phase 3.2 Batter CPRI rankings.
    Core methodology enhancements:
    1. Robust Adaptability Normalization:
       Replaces linear min-max scaling with robust sigmoid scaling
       to eliminate extreme tail saturation and prevent lower-order outlier
       spikes from compressing the core distribution of batters.
    2. Strict Sample Eligibility for Official Top 10:
       Requires N_pressure >= 100, M_pressure >= 8, and N_total >= 150
       for High Confidence. Demotes small-sample outliers (e.g. Karun Nair, Shan Masood)
       to Moderate Confidence while retaining them in the complete rankings.
    3. Retains Validated Dismissal Survival Contribution:
       Dismissal survival residual = expected_prob - actual_outcome
       Delivery contribution = +12.0 * survival_residual
    4. Player-Specific Consistency:
       50% positive pressure-match ratio + 30% mean residual rate + 20% stability.
    """
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
        
    d['is_pressure'] = d['pressure_score'].ge(pressure_threshold)
    
    # Delivery-level net impact:
    d['delivery_survival_contribution'] = d['batting_dismissal_residual']
    d['delivery_net_impact'] = (
        d['batting_run_residual'] + 
        wicket_value * d['delivery_survival_contribution'] + 
        wpa_multiplier * d['batting_wpa']
    )
    
    # 1. Match-level aggregates (filtered to matches where batter faced pressure deliveries)
    p_delivs = d[d['is_pressure']].copy()
    p_match_grp = p_delivs.groupby(['striker_id', 'striker_name_clean', 'competition_scope', 'match_id']).agg(
        match_pressure_balls=('actual_batter_runs', 'count'),
        match_run_res=('batting_run_residual', 'sum'),
        match_surv_res=('delivery_survival_contribution', 'sum'),
        match_wpa=('batting_wpa', 'sum'),
        match_net_impact=('delivery_net_impact', 'sum')
    ).reset_index()
    
    # Match net impact per 100 balls in pressure
    p_match_grp['match_impact_rate'] = (
        p_match_grp['match_net_impact'] / p_match_grp['match_pressure_balls']
    ) * 100.0
    
    # Player consistency metrics across pressure matches
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
    
    # 2. Player-level aggregates
    records = []
    for (pid, pname, scope), grp in d.groupby(['striker_id', 'striker_name_clean', 'competition_scope']):
        total_balls = len(grp)
        total_matches = grp['match_id'].nunique()
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        
        # Pressure Impact metrics
        p_run_res = p_grp['batting_run_residual'].sum() if p_balls > 0 else 0.0
        p_surv_res = p_grp['delivery_survival_contribution'].sum() if p_balls > 0 else 0.0
        p_wpa = p_grp['batting_wpa'].sum() if p_balls > 0 else 0.0
        
        p_rate_runs = (p_run_res / max(1, p_balls)) * 100.0
        p_rate_surv = (p_surv_res / max(1, p_balls)) * 100.0
        p_rate_wpa = (p_wpa / max(1, p_balls)) * 100.0
        
        raw_pressure_impact = p_rate_runs + wicket_value * p_rate_surv + wpa_multiplier * p_rate_wpa
        
        # Non-pressure Impact metrics
        np_run_res = np_grp['batting_run_residual'].sum() if np_balls > 0 else 0.0
        np_surv_res = np_grp['delivery_survival_contribution'].sum() if np_balls > 0 else 0.0
        np_wpa = np_grp['batting_wpa'].sum() if np_balls > 0 else 0.0
        
        np_rate_runs = (np_run_res / max(1, np_balls)) * 100.0
        np_rate_surv = (np_surv_res / max(1, np_balls)) * 100.0
        np_rate_wpa = (np_wpa / max(1, np_balls)) * 100.0
        raw_np_impact = np_rate_runs + wicket_value * np_rate_surv + wpa_multiplier * np_rate_wpa
        
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
            'raw_nonpressure_impact': raw_np_impact,
            'raw_adaptability': raw_adaptability,
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
    
    # 3. Apply Empirical Bayes Shrinkage and Robust Normalization per Scope
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
        
        # Component Scores [0, 100]
        g['score_pressure_impact'] = min_max_normalize(g['shrunk_pressure_impact'])
        # Robust sigmoid normalization for adaptability:
        g['score_adaptability'] = robust_sigmoid_normalize(g['shrunk_adaptability'], k=0.6)
        # Keep Phase 3.1 min-max for diagnostic comparison:
        g['score_adaptability_p31_minmax'] = min_max_normalize(g['shrunk_adaptability'])
        g['score_consistency'] = min_max_normalize(g['shrunk_consistency'])
        g['score_reliability'] = calculate_pressure_reliability(g['pressure_deliveries'], g['pressure_matches'])
        
        # Composite CPRI
        g['cpri_score'] = (
            weights['pressure_impact'] * g['score_pressure_impact'] +
            weights['adaptability'] * g['score_adaptability'] +
            weights['consistency'] * g['score_consistency'] +
            weights['reliability'] * g['score_reliability']
        ).round(2)
        
        # Confidence Tier assignment:
        g['confidence_tier'] = assign_batter_eligibility_tier(
            g['total_deliveries'], g['pressure_deliveries'], g['pressure_matches'],
            high_pball=100, high_pmatch=8, high_totball=150
        )
        g = g.sort_values('cpri_score', ascending=False).reset_index(drop=True)
        g['rank'] = g.index + 1
        scoped_summaries.append(g)
        
    all_batters = pd.concat(scoped_summaries, ignore_index=True)
    return all_batters, p_match_grp
