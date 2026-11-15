# ml/phase3_1/sensitivity_analysis.py
# Phase 3.1: Rigorous Sensitivity Analysis across Wicket Values, WPA Multipliers, Pressure Thresholds, and Weights.
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ml.phase3_1.cpri_batter import compute_batter_cpri_31
from ml.phase3_1.cpri_bowler import compute_bowler_cpri_31

BASE_DIR = Path(__file__).resolve().parent.parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3_1'

def safe_spearman(x: pd.Series, y: pd.Series) -> float:
    if len(x) < 2 or np.all(x == x.iloc[0]) or np.all(y == y.iloc[0]):
        return 1.0
    val, _ = spearmanr(x, y)
    return 1.0 if np.isnan(val) else float(val)

def run_coefficient_sensitivity_analysis():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print('Loading Phase 2 deliverable datasets for sensitivity analysis...')
    bat_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv', low_memory=False)
    wpa_deliv = pd.read_csv(BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv', low_memory=False)
    
    # 1. Baseline Phase 3.1 Models (Wicket Val=12.0, WPA Mult=25.0, Pressure Thresh=50.0)
    base_bat, _ = compute_batter_cpri_31(bat_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=25.0, pressure_threshold=50.0)
    base_bowl, _ = compute_bowler_cpri_31(bowl_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=25.0, pressure_threshold=50.0)
    
    records = []
    
    # Test Parameters
    wicket_values = [8.0, 10.0, 12.0, 14.0, 16.0]
    wpa_multipliers = [10.0, 15.0, 20.0, 25.0, 30.0]
    pressure_thresholds = [40.0, 45.0, 50.0, 55.0, 60.0]
    
    # A. Wicket Replacement Value Variations
    print("Testing wicket replacement values...")
    for wv in wicket_values:
        alt_bat, _ = compute_batter_cpri_31(bat_deliv, wpa_deliv, wicket_value=wv, wpa_multiplier=25.0, pressure_threshold=50.0)
        alt_bowl, _ = compute_bowler_cpri_31(bowl_deliv, wpa_deliv, wicket_value=wv, wpa_multiplier=25.0, pressure_threshold=50.0)
        
        for scope in ['IPL', 'T20I']:
            # Batters
            b_base_s = base_bat[(base_bat['competition_scope'] == scope) & (base_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            b_alt_s = alt_bat[(alt_bat['competition_scope'] == scope) & (alt_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_b = b_base_s[['player_id', 'rank']].merge(b_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_b = safe_spearman(m_b['rank_base'], m_b['rank_alt'])
            top10_b = len(set(b_base_s.head(10)['player_id']).intersection(set(b_alt_s.head(10)['player_id'])))
            
            # Bowlers
            bw_base_s = base_bowl[(base_bowl['competition_scope'] == scope) & (base_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            bw_alt_s = alt_bowl[(alt_bowl['competition_scope'] == scope) & (alt_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_bw = bw_base_s[['player_id', 'rank']].merge(bw_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_bw = safe_spearman(m_bw['rank_base'], m_bw['rank_alt'])
            top10_bw = len(set(bw_base_s.head(10)['player_id']).intersection(set(bw_alt_s.head(10)['player_id'])))
            
            records.append({
                'parameter_type': 'Wicket Value',
                'parameter_value': wv,
                'competition_scope': scope,
                'role': 'Batter',
                'eligible_population': len(b_base_s),
                'spearman_rank_correlation': round(rho_b, 4),
                'top10_overlap_count': top10_b,
                'high_tier_count': len(b_alt_s)
            })
            records.append({
                'parameter_type': 'Wicket Value',
                'parameter_value': wv,
                'competition_scope': scope,
                'role': 'Bowler',
                'eligible_population': len(bw_base_s),
                'spearman_rank_correlation': round(rho_bw, 4),
                'top10_overlap_count': top10_bw,
                'high_tier_count': len(bw_alt_s)
            })
            
    # B. WPA Multipliers Variations
    print("Testing WPA multipliers...")
    for wm in wpa_multipliers:
        alt_bat, _ = compute_batter_cpri_31(bat_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=wm, pressure_threshold=50.0)
        alt_bowl, _ = compute_bowler_cpri_31(bowl_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=wm, pressure_threshold=50.0)
        
        for scope in ['IPL', 'T20I']:
            b_base_s = base_bat[(base_bat['competition_scope'] == scope) & (base_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            b_alt_s = alt_bat[(alt_bat['competition_scope'] == scope) & (alt_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_b = b_base_s[['player_id', 'rank']].merge(b_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_b = safe_spearman(m_b['rank_base'], m_b['rank_alt'])
            top10_b = len(set(b_base_s.head(10)['player_id']).intersection(set(b_alt_s.head(10)['player_id'])))
            
            bw_base_s = base_bowl[(base_bowl['competition_scope'] == scope) & (base_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            bw_alt_s = alt_bowl[(alt_bowl['competition_scope'] == scope) & (alt_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_bw = bw_base_s[['player_id', 'rank']].merge(bw_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_bw = safe_spearman(m_bw['rank_base'], m_bw['rank_alt'])
            top10_bw = len(set(bw_base_s.head(10)['player_id']).intersection(set(bw_alt_s.head(10)['player_id'])))
            
            records.append({
                'parameter_type': 'WPA Multiplier',
                'parameter_value': wm,
                'competition_scope': scope,
                'role': 'Batter',
                'eligible_population': len(b_base_s),
                'spearman_rank_correlation': round(rho_b, 4),
                'top10_overlap_count': top10_b,
                'high_tier_count': len(b_alt_s)
            })
            records.append({
                'parameter_type': 'WPA Multiplier',
                'parameter_value': wm,
                'competition_scope': scope,
                'role': 'Bowler',
                'eligible_population': len(bw_base_s),
                'spearman_rank_correlation': round(rho_bw, 4),
                'top10_overlap_count': top10_bw,
                'high_tier_count': len(bw_alt_s)
            })
            
    # C. Pressure Thresholds Variations
    print("Testing pressure thresholds...")
    for pt in pressure_thresholds:
        alt_bat, _ = compute_batter_cpri_31(bat_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=25.0, pressure_threshold=pt)
        alt_bowl, _ = compute_bowler_cpri_31(bowl_deliv, wpa_deliv, wicket_value=12.0, wpa_multiplier=25.0, pressure_threshold=pt)
        
        for scope in ['IPL', 'T20I']:
            b_base_s = base_bat[(base_bat['competition_scope'] == scope) & (base_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            b_alt_s = alt_bat[(alt_bat['competition_scope'] == scope) & (alt_bat['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_b = b_base_s[['player_id', 'rank']].merge(b_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_b = safe_spearman(m_b['rank_base'], m_b['rank_alt'])
            top10_b = len(set(b_base_s.head(10)['player_id']).intersection(set(b_alt_s.head(10)['player_id'])))
            
            bw_base_s = base_bowl[(base_bowl['competition_scope'] == scope) & (base_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            bw_alt_s = alt_bowl[(alt_bowl['competition_scope'] == scope) & (alt_bowl['confidence_tier'] == 'High Confidence')].sort_values('rank').reset_index(drop=True)
            m_bw = bw_base_s[['player_id', 'rank']].merge(bw_alt_s[['player_id', 'rank']], on='player_id', suffixes=('_base', '_alt'))
            rho_bw = safe_spearman(m_bw['rank_base'], m_bw['rank_alt'])
            top10_bw = len(set(bw_base_s.head(10)['player_id']).intersection(set(bw_alt_s.head(10)['player_id'])))
            
            records.append({
                'parameter_type': 'Pressure Threshold',
                'parameter_value': pt,
                'competition_scope': scope,
                'role': 'Batter',
                'eligible_population': len(b_base_s),
                'spearman_rank_correlation': round(rho_b, 4),
                'top10_overlap_count': top10_b,
                'high_tier_count': len(b_alt_s)
            })
            records.append({
                'parameter_type': 'Pressure Threshold',
                'parameter_value': pt,
                'competition_scope': scope,
                'role': 'Bowler',
                'eligible_population': len(bw_base_s),
                'spearman_rank_correlation': round(rho_bw, 4),
                'top10_overlap_count': top10_bw,
                'high_tier_count': len(bw_alt_s)
            })
            
    df_res = pd.DataFrame(records)
    df_res.to_csv(OUT_DIR / 'phase3_1_coefficient_sensitivity.csv', index=False)
    print("Saved phase3_1_coefficient_sensitivity.csv successfully!")
    return df_res

if __name__ == '__main__':
    run_coefficient_sensitivity_analysis()
