# ranking_engine.py
# Phase 3: Final CPRI Ranking Pipeline, Bootstrap Confidence Intervals & Export Engine.
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ml.phase3.cpri_batter import compute_batter_cpri
from ml.phase3.cpri_bowler import compute_bowler_cpri

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3'

def compute_bootstrap_confidence_intervals(
    match_grp: pd.DataFrame,
    id_col: str,
    name_col: str,
    metric_col: str,
    n_bootstrap: int = 150,
    random_state: int = 42
) -> pd.DataFrame:
    rng = np.random.RandomState(random_state)
    records = []
    
    for (pid, pname, scope), grp in match_grp.groupby([id_col, name_col, 'competition_scope']):
        matches = grp['match_id'].values
        n_m = len(matches)
        if n_m < 3:
            # Insufficient matches for robust bootstrap
            val = grp[metric_col].mean()
            records.append({
                'player_id': pid, 'player_name': pname, 'competition_scope': scope,
                'ci_lower_95': round(float(val - 10.0), 2),
                'ci_upper_95': round(float(val + 10.0), 2),
                'ci_std_error': 5.0
            })
            continue
            
        boot_means = []
        metric_vals = grp[metric_col].values
        for _ in range(n_bootstrap):
            idx = rng.choice(n_m, size=n_m, replace=True)
            boot_means.append(np.mean(metric_vals[idx]))
            
        ci_low = np.percentile(boot_means, 2.5)
        ci_high = np.percentile(boot_means, 97.5)
        std_err = np.std(boot_means)
        
        records.append({
            'player_id': pid, 'player_name': pname, 'competition_scope': scope,
            'ci_lower_95': round(float(ci_low), 2),
            'ci_upper_95': round(float(ci_high), 2),
            'ci_std_error': round(float(std_err), 2)
        })
        
    return pd.DataFrame(records)

def run_ranking_pipeline():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    print('Loading Phase 2 deliverable datasets...')
    bat_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv', low_memory=False)
    wpa_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv', low_memory=False)
    
    # 2. Compute CPRI for Batters
    print('Computing Batter CPRI rankings...')
    batters_df, b_match_grp = compute_batter_cpri(bat_deliv, wpa_deliv)
    
    # 3. Compute CPRI for Bowlers
    print('Computing Bowler CPRI rankings...')
    bowlers_df, bw_match_grp = compute_bowler_cpri(bowl_deliv, wpa_deliv)
    
    # 4. Bootstrap Confidence Intervals
    print('Calculating Bootstrap Confidence Intervals...')
    b_ci = compute_bootstrap_confidence_intervals(b_match_grp, 'striker_id', 'striker_name_clean', 'match_net_impact_rate')
    b_ci['role'] = 'Batter'
    bw_ci = compute_bootstrap_confidence_intervals(bw_match_grp, 'bowler_id', 'bowler_name_clean', 'match_net_impact_rate')
    bw_ci['role'] = 'Bowler'
    all_ci = pd.concat([b_ci, bw_ci], ignore_index=True)
    all_ci.to_csv(OUT_DIR / 'ranking_confidence_intervals.csv', index=False)
    print('Saved ranking_confidence_intervals.csv!')
    
    # 5. Extract Top 10 by Scope
    # Eligible for Official Top 10: High Confidence (>= 150 deliveries)
    top10_batters_list = []
    for scope in ['IPL', 'T20I']:
        sub = batters_df[(batters_df['competition_scope'] == scope) & 
                         (batters_df['confidence_tier'] == 'High Confidence')].head(10).copy()
        sub['official_rank'] = range(1, len(sub) + 1)
        top10_batters_list.append(sub)
    top10_batters = pd.concat(top10_batters_list, ignore_index=True)
    top10_batters.to_csv(OUT_DIR / 'top10_batters.csv', index=False)
    print('Saved top10_batters.csv!')
    
    top10_bowlers_list = []
    for scope in ['IPL', 'T20I']:
        sub = bowlers_df[(bowlers_df['competition_scope'] == scope) & 
                         (bowlers_df['confidence_tier'] == 'High Confidence')].head(10).copy()
        sub['official_rank'] = range(1, len(sub) + 1)
        top10_bowlers_list.append(sub)
    top10_bowlers = pd.concat(top10_bowlers_list, ignore_index=True)
    top10_bowlers.to_csv(OUT_DIR / 'top10_bowlers.csv', index=False)
    print('Saved top10_bowlers.csv!')
    
    # 6. Export Full Population Rankings
    batters_df.to_csv(OUT_DIR / 'all_batter_rankings.csv', index=False)
    bowlers_df.to_csv(OUT_DIR / 'all_bowler_rankings.csv', index=False)
    print('Saved all_batter_rankings.csv and all_bowler_rankings.csv!')
    
    # 7. Export CPRI Component Scores
    bat_comp = batters_df[[
        'player_id', 'player_name', 'competition_scope', 'total_deliveries', 'confidence_tier',
        'score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability', 'cpri_score'
    ]].copy()
    bat_comp['role'] = 'Batter'
    
    bowl_comp = bowlers_df[[
        'player_id', 'player_name', 'competition_scope', 'total_deliveries', 'confidence_tier',
        'score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability', 'cpri_score'
    ]].copy()
    bowl_comp['role'] = 'Bowler'
    
    comp_scores = pd.concat([bat_comp, bowl_comp], ignore_index=True)
    comp_scores.to_csv(OUT_DIR / 'cpri_component_scores.csv', index=False)
    print('Saved cpri_component_scores.csv!')
    
    print('Phase 3 CPRI ranking pipeline completed successfully!')
    return batters_df, bowlers_df

if __name__ == '__main__':
    run_ranking_pipeline()
