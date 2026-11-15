#!/usr/bin/env python3
'''
pressure_validation.py
Validation and evaluation routines for Phase 2A Dynamic Pressure Engine.
Generates pressure distributions, phase breakdowns, match outcome correlations, and exports deliverables.
'''
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from ml.phase2.pressure_engine import DynamicPressureEngine

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_FILE = BASE_DIR / 'output' / 'processed' / 'deliveries_enriched.csv'
MATCHES_FILE = BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv'
OUTPUT_DIR = BASE_DIR / 'output' / 'phase2'

def run_validation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Loading data from {PROCESSED_FILE}...')
    df = pd.read_csv(PROCESSED_FILE, low_memory=False)
    matches = pd.read_csv(MATCHES_FILE, low_memory=False)
    
    # Identify abandoned matches to exclude from training
    abandoned_matches = set(matches[matches.result.str.contains('Abandon|No result', case=False, na=False)].match_id)
    print(f'Identified {len(abandoned_matches)} abandoned matches to exclude from model training.')
    
    engine = DynamicPressureEngine()
    scored = engine.score_deliveries(df, abandoned_matches)
    
    # Exclude Emerging Teams T20 from official ranking/distribution outputs
    in_scope_scored = scored[scored.in_scope_competition.fillna(False)].copy()
    
    print('Saving pressure_scored_deliveries.csv...')
    scored.to_csv(OUTPUT_DIR / 'pressure_scored_deliveries.csv', index=False)
    
    # Generate Distribution Summary
    dist_summary = []
    
    # Overall distribution
    stats_overall = in_scope_scored['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
    dist_summary.append({
        'segment_type': 'Overall', 'segment_value': 'All In-Scope',
        'count': int(stats_overall['count']),
        'mean': round(stats_overall['mean'], 2),
        'std': round(stats_overall['std'], 2),
        'min': round(stats_overall['min'], 2),
        'p10': round(stats_overall['10%'], 2),
        'p25': round(stats_overall['25%'], 2),
        'median': round(stats_overall['50%'], 2),
        'p75': round(stats_overall['75%'], 2),
        'p90': round(stats_overall['90%'], 2),
        'max': round(stats_overall['max'], 2)
    })
    
    # Distribution by format
    for fmt, grp in in_scope_scored.groupby('competition_scope'):
        st = grp['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        dist_summary.append({
            'segment_type': 'Format', 'segment_value': fmt,
            'count': int(st['count']), 'mean': round(st['mean'], 2), 'std': round(st['std'], 2),
            'min': round(st['min'], 2), 'p10': round(st['10%'], 2), 'p25': round(st['25%'], 2),
            'median': round(st['50%'], 2), 'p75': round(st['75%'], 2), 'p90': round(st['90%'], 2),
            'max': round(st['max'], 2)
        })
        
    # Distribution by innings
    for inn, grp in in_scope_scored.groupby('innings'):
        if inn > 2: continue
        st = grp['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        dist_summary.append({
            'segment_type': 'Innings', 'segment_value': f'Innings {inn}',
            'count': int(st['count']), 'mean': round(st['mean'], 2), 'std': round(st['std'], 2),
            'min': round(st['min'], 2), 'p10': round(st['10%'], 2), 'p25': round(st['25%'], 2),
            'median': round(st['50%'], 2), 'p75': round(st['75%'], 2), 'p90': round(st['90%'], 2),
            'max': round(st['max'], 2)
        })
        
    # Distribution by innings phase
    for phase, grp in in_scope_scored.groupby('innings_phase'):
        st = grp['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        dist_summary.append({
            'segment_type': 'Phase', 'segment_value': phase,
            'count': int(st['count']), 'mean': round(st['mean'], 2), 'std': round(st['std'], 2),
            'min': round(st['min'], 2), 'p10': round(st['10%'], 2), 'p25': round(st['25%'], 2),
            'median': round(st['50%'], 2), 'p75': round(st['75%'], 2), 'p90': round(st['90%'], 2),
            'max': round(st['max'], 2)
        })
        
    # Distribution by wickets remaining (binned)
    in_scope_scored['wkt_bracket'] = pd.cut(
        in_scope_scored['wickets_in_hand'],
        bins=[-0.1, 3.0, 6.0, 10.0],
        labels=['Tail (1-3 wkts)', 'Middle (4-6 wkts)', 'Top (7-10 wkts)']
    )
    for wkt_b, grp in in_scope_scored.groupby('wkt_bracket', observed=False):
        st = grp['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        dist_summary.append({
            'segment_type': 'Wickets in Hand', 'segment_value': str(wkt_b),
            'count': int(st['count']), 'mean': round(st['mean'], 2), 'std': round(st['std'], 2),
            'min': round(st['min'], 2), 'p10': round(st['10%'], 2), 'p25': round(st['25%'], 2),
            'median': round(st['50%'], 2), 'p75': round(st['75%'], 2), 'p90': round(st['90%'], 2),
            'max': round(st['max'], 2)
        })
        
    # Distribution by RRR in Chase
    chase_df = in_scope_scored[in_scope_scored['innings'] == 2].copy()
    chase_df['rrr_bracket'] = pd.cut(
        chase_df['required_run_rate'],
        bins=[-0.1, 6.0, 9.0, 12.0, 15.0, 36.0],
        labels=['Low (<6 RPO)', 'Normal (6-9 RPO)', 'High (9-12 RPO)', 'Severe (12-15 RPO)', 'Extreme (>15 RPO)']
    )
    for rrr_b, grp in chase_df.groupby('rrr_bracket', observed=False):
        st = grp['pressure_score'].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        dist_summary.append({
            'segment_type': 'Chase RRR', 'segment_value': str(rrr_b),
            'count': int(st['count']), 'mean': round(st['mean'], 2), 'std': round(st['std'], 2),
            'min': round(st['min'], 2), 'p10': round(st['10%'], 2), 'p25': round(st['25%'], 2),
            'median': round(st['50%'], 2), 'p75': round(st['75%'], 2), 'p90': round(st['90%'], 2),
            'max': round(st['max'], 2)
        })
        
    dist_df = pd.DataFrame(dist_summary)
    dist_df.to_csv(OUTPUT_DIR / 'pressure_distribution.csv', index=False)
    print('Saved pressure_distribution.csv!')
    
    # Analyze relationship between pressure and match outcomes
    chase_outcomes = chase_df.merge(matches[['match_id', 'win_team_id']], on='match_id', how='left')
    chase_outcomes['batting_won'] = (chase_outcomes['win_team_id_y'] == chase_outcomes['batting_team_id']).astype(int)
    
    # Calculate win rate by pressure tier in the 2nd innings
    tier_win_rate = chase_outcomes.groupby('pressure_tier', observed=False)['batting_won'].agg(['count', 'mean']).reset_index()
    tier_win_rate.columns = ['pressure_tier', 'delivery_count', 'chasing_team_win_rate']
    print('\nChasing Team Win Rate by Pressure Tier:')
    print(tier_win_rate)
    
    print('\nValidation script execution completed successfully.')

if __name__ == '__main__':
    run_validation()
