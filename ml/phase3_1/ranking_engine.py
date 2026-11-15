# ml/phase3_1/ranking_engine.py
# Phase 3.1: Final Refined CPRI Ranking Pipeline, Bootstrap Confidence Intervals & Deliverable Exporter.
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from ml.phase3_1.cpri_batter import compute_batter_cpri_31
from ml.phase3_1.cpri_bowler import compute_bowler_cpri_31

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3_1'
ORIG_DIR = BASE_DIR / 'output' / 'phase3'

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

def run_ranking_pipeline_31():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print('Loading Phase 2 deliverable datasets...')
    bat_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv', low_memory=False)
    wpa_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv', low_memory=False)
    
    # 1. Compute Phase 3.1 CPRI for Batters
    print('Computing Refined Batter CPRI rankings...')
    batters_df, b_match_grp = compute_batter_cpri_31(bat_deliv, wpa_deliv)
    
    # 2. Compute Phase 3.1 CPRI for Bowlers
    print('Computing Refined Bowler CPRI rankings...')
    bowlers_df, bw_match_grp = compute_bowler_cpri_31(bowl_deliv, wpa_deliv)
    
    # 3. Bootstrap Confidence Intervals
    print('Calculating Bootstrap Confidence Intervals...')
    b_ci = compute_bootstrap_confidence_intervals(b_match_grp, 'striker_id', 'striker_name_clean', 'match_impact_rate')
    b_ci['role'] = 'Batter'
    bw_ci = compute_bootstrap_confidence_intervals(bw_match_grp, 'bowler_id', 'bowler_name_clean', 'match_impact_rate')
    bw_ci['role'] = 'Bowler'
    all_ci = pd.concat([b_ci, bw_ci], ignore_index=True)
    all_ci.to_csv(OUT_DIR / 'ranking_confidence_intervals.csv', index=False)
    print('Saved ranking_confidence_intervals.csv!')
    
    # 4. Extract Top 10 by Scope (High Confidence: p_balls >= 50, p_matches >= 3, total_balls >= 100)
    top10_batters_list = []
    for scope in ['IPL', 'T20I']:
        sub = batters_df[(batters_df['competition_scope'] == scope) & 
                         (batters_df['confidence_tier'] == 'High Confidence')].sort_values('cpri_score', ascending=False).head(10).copy()
        sub['official_rank'] = range(1, len(sub) + 1)
        top10_batters_list.append(sub)
    top10_batters = pd.concat(top10_batters_list, ignore_index=True)
    top10_batters.to_csv(OUT_DIR / 'top10_batters.csv', index=False)
    print('Saved top10_batters.csv!')
    
    top10_bowlers_list = []
    for scope in ['IPL', 'T20I']:
        sub = bowlers_df[(bowlers_df['competition_scope'] == scope) & 
                         (bowlers_df['confidence_tier'] == 'High Confidence')].sort_values('cpri_score', ascending=False).head(10).copy()
        sub['official_rank'] = range(1, len(sub) + 1)
        top10_bowlers_list.append(sub)
    top10_bowlers = pd.concat(top10_bowlers_list, ignore_index=True)
    top10_bowlers.to_csv(OUT_DIR / 'top10_bowlers.csv', index=False)
    print('Saved top10_bowlers.csv!')
    
    # 5. Export Full Population Rankings
    batters_df.to_csv(OUT_DIR / 'all_batter_rankings.csv', index=False)
    bowlers_df.to_csv(OUT_DIR / 'all_bowler_rankings.csv', index=False)
    print('Saved all_batter_rankings.csv and all_bowler_rankings.csv!')
    
    # 6. Export CPRI Component Scores
    bat_comp = batters_df[[
        'player_id', 'player_name', 'competition_scope', 'total_deliveries', 'pressure_deliveries', 'pressure_matches', 'confidence_tier',
        'score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability', 'cpri_score'
    ]].copy()
    bat_comp['role'] = 'Batter'
    
    bowl_comp = bowlers_df[[
        'player_id', 'player_name', 'competition_scope', 'total_deliveries', 'pressure_deliveries', 'pressure_matches', 'confidence_tier',
        'score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability', 'cpri_score'
    ]].copy()
    bowl_comp['role'] = 'Bowler'
    
    comp_scores = pd.concat([bat_comp, bowl_comp], ignore_index=True)
    comp_scores.to_csv(OUT_DIR / 'cpri_component_scores.csv', index=False)
    print('Saved cpri_component_scores.csv!')
    
    # 7. Generate phase3_1_reliability_analysis.csv
    print('Generating reliability analysis report...')
    b_rel = batters_df[['player_id', 'player_name', 'competition_scope', 'total_deliveries', 'pressure_deliveries', 'pressure_matches', 'score_reliability', 'confidence_tier']].copy()
    b_rel['role'] = 'Batter'
    bw_rel = bowlers_df[['player_id', 'player_name', 'competition_scope', 'total_deliveries', 'pressure_deliveries', 'pressure_matches', 'score_reliability', 'confidence_tier']].copy()
    bw_rel['role'] = 'Bowler'
    rel_analysis = pd.concat([b_rel, bw_rel], ignore_index=True)
    rel_analysis.to_csv(OUT_DIR / 'phase3_1_reliability_analysis.csv', index=False)
    print('Saved phase3_1_reliability_analysis.csv!')
    
    # 8. Generate phase3_1_ranking_comparison.csv (Original Phase 3 vs Refined Phase 3.1)
    print('Generating ranking comparison report between Phase 3 and Phase 3.1...')
    orig_top_bat = pd.read_csv(ORIG_DIR / 'top10_batters.csv')
    orig_top_bowl = pd.read_csv(ORIG_DIR / 'top10_bowlers.csv')
    orig_all_bat = pd.read_csv(ORIG_DIR / 'all_batter_rankings.csv')
    orig_all_bowl = pd.read_csv(ORIG_DIR / 'all_bowler_rankings.csv')
    
    comp_records = []
    for scope in ['IPL', 'T20I']:
        # Batter comparison
        b_p3 = orig_all_bat[orig_all_bat['competition_scope'] == scope].set_index('player_id')
        b_p31 = batters_df[batters_df['competition_scope'] == scope].set_index('player_id')
        common_b = b_p3.index.intersection(b_p31.index)
        
        for pid in common_b:
            pname = b_p31.loc[pid, 'player_name']
            r_p3 = int(b_p3.loc[pid, 'rank'])
            r_p31 = int(b_p31.loc[pid, 'rank'])
            c_p3 = float(b_p3.loc[pid, 'cpri_score'])
            c_p31 = float(b_p31.loc[pid, 'cpri_score'])
            t_p3 = b_p3.loc[pid, 'confidence_tier']
            t_p31 = b_p31.loc[pid, 'confidence_tier']
            comp_records.append({
                'player_id': pid,
                'player_name': pname,
                'competition_scope': scope,
                'role': 'Batter',
                'p3_rank': r_p3,
                'p31_rank': r_p31,
                'rank_change': r_p3 - r_p31, # positive = improved rank
                'p3_cpri': c_p3,
                'p31_cpri': c_p31,
                'p3_tier': t_p3,
                'p31_tier': t_p31
            })
            
        # Bowler comparison
        bw_p3 = orig_all_bowl[orig_all_bowl['competition_scope'] == scope].set_index('player_id')
        bw_p31 = bowlers_df[bowlers_df['competition_scope'] == scope].set_index('player_id')
        common_bw = bw_p3.index.intersection(bw_p31.index)
        
        for pid in common_bw:
            pname = bw_p31.loc[pid, 'player_name']
            r_p3 = int(bw_p3.loc[pid, 'rank'])
            r_p31 = int(bw_p31.loc[pid, 'rank'])
            c_p3 = float(bw_p3.loc[pid, 'cpri_score'])
            c_p31 = float(bw_p31.loc[pid, 'cpri_score'])
            t_p3 = bw_p3.loc[pid, 'confidence_tier']
            t_p31 = bw_p31.loc[pid, 'confidence_tier']
            comp_records.append({
                'player_id': pid,
                'player_name': pname,
                'competition_scope': scope,
                'role': 'Bowler',
                'p3_rank': r_p3,
                'p31_rank': r_p31,
                'rank_change': r_p3 - r_p31,
                'p3_cpri': c_p3,
                'p31_cpri': c_p31,
                'p3_tier': t_p3,
                'p31_tier': t_p31
            })
            
    comp_df = pd.DataFrame(comp_records)
    comp_df.to_csv(OUT_DIR / 'phase3_1_ranking_comparison.csv', index=False)
    print('Saved phase3_1_ranking_comparison.csv!')
    
    print('Phase 3.1 CPRI ranking pipeline completed successfully!')
    return batters_df, bowlers_df

if __name__ == '__main__':
    run_ranking_pipeline_31()
