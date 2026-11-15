# sensitivity_analysis.py
# Phase 3: Sensitivity Analysis across Weights, Pressure Thresholds, WPA inclusion, and Eligibility.
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ml.phase3.cpri_batter import compute_batter_cpri
from ml.phase3.cpri_bowler import compute_bowler_cpri

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3'

def run_sensitivity_analysis():
    print('Loading datasets for sensitivity analysis...')
    bat_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv', low_memory=False)
    wpa_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv', low_memory=False)
    
    # 1. Base CPRI
    base_bat, _ = compute_batter_cpri(bat_deliv, wpa_deliv)
    base_bowl, _ = compute_bowler_cpri(bowl_deliv, wpa_deliv)
    
    # Define Weight Schemes
    weight_schemes = {
        'Baseline (40/25/20/15)': {'pressure_impact': 0.40, 'adaptability': 0.25, 'consistency': 0.20, 'reliability': 0.15},
        'Impact Heavy (55/15/15/15)': {'pressure_impact': 0.55, 'adaptability': 0.15, 'consistency': 0.15, 'reliability': 0.15},
        'Equal Weights (25/25/25/25)': {'pressure_impact': 0.25, 'adaptability': 0.25, 'consistency': 0.25, 'reliability': 0.25},
        'Consistency Heavy (30/20/35/15)': {'pressure_impact': 0.30, 'adaptability': 0.20, 'consistency': 0.35, 'reliability': 0.15},
        'High Reliability (30/20/15/35)': {'pressure_impact': 0.30, 'adaptability': 0.20, 'consistency': 0.15, 'reliability': 0.35}
    }
    
    records = []
    
    # Evaluate across schemes
    for s_name, w_dict in weight_schemes.items():
        alt_bat, _ = compute_batter_cpri(bat_deliv, wpa_deliv, weights=w_dict)
        alt_bowl, _ = compute_bowler_cpri(bowl_deliv, wpa_deliv, weights=w_dict)
        
        for scope in ['IPL', 'T20I']:
            # Batters (High Confidence)
            b_base_scope = base_bat[(base_bat['competition_scope'] == scope) & (base_bat['confidence_tier'] == 'High Confidence')]
            b_alt_scope = alt_bat[(alt_bat['competition_scope'] == scope) & (alt_bat['confidence_tier'] == 'High Confidence')]
            merged_b = b_base_scope[['player_id', 'rank']].merge(b_alt_scope[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_b, _ = spearmanr(merged_b['rank_base'], merged_b['rank_alt'])
            
            # Bowlers (High Confidence)
            bw_base_scope = base_bowl[(base_bowl['competition_scope'] == scope) & (base_bowl['confidence_tier'] == 'High Confidence')]
            bw_alt_scope = alt_bowl[(alt_bowl['competition_scope'] == scope) & (alt_bowl['confidence_tier'] == 'High Confidence')]
            merged_bw = bw_base_scope[['player_id', 'rank']].merge(bw_alt_scope[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_bw, _ = spearmanr(merged_bw['rank_base'], merged_bw['rank_alt'])
            
            records.append({
                'weight_scheme': s_name,
                'competition_scope': scope,
                'role': 'Batter',
                'spearman_rank_correlation': round(float(rho_b), 4),
                'top10_overlap_count': len(set(b_base_scope.head(10)['player_id']).intersection(set(b_alt_scope.head(10)['player_id']))),
                'weights_description': str(w_dict)
            })
            records.append({
                'weight_scheme': s_name,
                'competition_scope': scope,
                'role': 'Bowler',
                'spearman_rank_correlation': round(float(rho_bw), 4),
                'top10_overlap_count': len(set(bw_base_scope.head(10)['player_id']).intersection(set(bw_alt_scope.head(10)['player_id']))),
                'weights_description': str(w_dict)
            })
            
    report_df = pd.DataFrame(records)
    report_df.to_csv(OUT_DIR / 'weight_sensitivity_report.csv', index=False)
    print('Saved weight_sensitivity_report.csv!')
    return report_df

if __name__ == '__main__':
    run_sensitivity_analysis()
