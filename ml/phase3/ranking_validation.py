# ranking_validation.py
# Phase 3: Comprehensive Ranking Validation & Stability Audit.
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ml.phase3.cpri_batter import compute_batter_cpri
from ml.phase3.cpri_bowler import compute_bowler_cpri

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3'

def run_ranking_validation():
    print('Loading Phase 2 datasets for comprehensive validation...')
    bat_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv', low_memory=False)
    wpa_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv', low_memory=False)
    
    # 1. Base CPRI
    base_bat, _ = compute_batter_cpri(bat_deliv, wpa_deliv)
    base_bowl, _ = compute_bowler_cpri(bowl_deliv, wpa_deliv)
    
    # 2. Ranking with and without WPA
    wpa_zero = wpa_deliv.copy()
    wpa_zero['batting_wpa'] = 0.0
    wpa_zero['bowling_wpa'] = 0.0
    
    no_wpa_bat, _ = compute_batter_cpri(bat_deliv, wpa_zero)
    no_wpa_bowl, _ = compute_bowler_cpri(bowl_deliv, wpa_zero)
    
    validation_records = []
    for scope in ['IPL', 'T20I']:
        # Batter WPA impact
        b_base = base_bat[(base_bat['competition_scope'] == scope) & (base_bat['confidence_tier'] == 'High Confidence')]
        b_no_wpa = no_wpa_bat[(no_wpa_bat['competition_scope'] == scope) & (no_wpa_bat['confidence_tier'] == 'High Confidence')]
        merged_b = b_base[['player_id', 'rank']].merge(b_no_wpa[['player_id', 'rank']], on='player_id', suffixes=('_base', '_no_wpa'))
        rho_b, _ = spearmanr(merged_b['rank_base'], merged_b['rank_no_wpa'])
        overlap_b = len(set(b_base.head(10)['player_id']).intersection(set(b_no_wpa.head(10)['player_id'])))
        
        # Bowler WPA impact
        bw_base = base_bowl[(base_bowl['competition_scope'] == scope) & (base_bowl['confidence_tier'] == 'High Confidence')]
        bw_no_wpa = no_wpa_bowl[(no_wpa_bowl['competition_scope'] == scope) & (no_wpa_bowl['confidence_tier'] == 'High Confidence')]
        merged_bw = bw_base[['player_id', 'rank']].merge(bw_no_wpa[['player_id', 'rank']], on='player_id', suffixes=('_base', '_no_wpa'))
        rho_bw, _ = spearmanr(merged_bw['rank_base'], merged_bw['rank_no_wpa'])
        overlap_bw = len(set(bw_base.head(10)['player_id']).intersection(set(bw_no_wpa.head(10)['player_id'])))
        
        validation_records.append({
            'test_condition': 'WPA Excluded vs Included',
            'competition_scope': scope,
            'role': 'Batter',
            'spearman_rank_correlation': round(float(rho_b), 4),
            'top10_overlap_count': overlap_b
        })
        validation_records.append({
            'test_condition': 'WPA Excluded vs Included',
            'competition_scope': scope,
            'role': 'Bowler',
            'spearman_rank_correlation': round(float(rho_bw), 4),
            'top10_overlap_count': overlap_bw
        })
        
    print('Validation Records:')
    for r in validation_records:
        print(r)
        
    return validation_records

if __name__ == '__main__':
    run_ranking_validation()
