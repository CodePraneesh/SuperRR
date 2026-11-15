#!/usr/bin/env python3
'''
pressure_features.py
Feature extraction and pre-delivery state engineering for Phase 2A Dynamic Pressure Engine.
Strictly ensures zero future-ball and zero current-delivery leakage.
'''
from __future__ import annotations
import numpy as np
import pandas as pd

def extract_predelivery_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Validates and extracts pre-delivery features for 1st innings and chasing models.
    All inputs are strictly pre-delivery.
    '''
    df = df.copy()
    
    # 1. Base Pre-delivery Metrics (guaranteed shifted)
    # balls_remaining: remaining legal balls in the innings
    if 'balls_remaining' not in df.columns:
        df['balls_remaining'] = np.maximum(0, (df['overs_limit'] * 6 - df['legal_balls_before']).fillna(0))
    
    # wickets_in_hand
    if 'wickets_in_hand' not in df.columns:
        df['wickets_in_hand'] = np.maximum(0, 10 - df['wickets_lost_before'])
        
    # overs_elapsed
    if 'overs_elapsed' not in df.columns:
        df['overs_elapsed'] = df['legal_balls_before'] / 6.0
        
    # current_run_rate (safe divide)
    if 'current_run_rate' not in df.columns:
        df['current_run_rate'] = np.where(
            df['legal_balls_before'] > 0,
            df['score_before'] / (df['legal_balls_before'] / 6.0),
            np.nan
        )
    # Fill ball 1 CRR with 8.0 (typical baseline league run rate)
    df['crr_clean'] = df['current_run_rate'].fillna(8.0).clip(0, 36.0)
    
    # 2. Phase Encoding
    if 'innings_phase' not in df.columns:
        death_start = np.maximum(0, df['overs_limit'] - 5)
        df['innings_phase'] = np.select(
            [df['innings'] >= 3, df['overs_elapsed'] < np.minimum(6, df['overs_limit']),
             df['overs_elapsed'] >= death_start],
            ['super_over_or_extra', 'powerplay', 'death'], default='middle')
            
    df['is_powerplay'] = df['innings_phase'].eq('powerplay').astype(int)
    df['is_middle'] = df['innings_phase'].eq('middle').astype(int)
    df['is_death'] = df['innings_phase'].eq('death').astype(int)
    
    # 3. Chasing-Specific Pre-delivery Metrics
    df['rrr_clean'] = df['required_run_rate'].fillna(0.0).clip(0, 36.0)
    df['runs_req_clean'] = df['runs_required'].fillna(0.0).clip(lower=0.0)
    df['target_clean'] = df['target_runs'].fillna(0.0)
    
    # Resource metrics (Clark/Duckworth-Lewis style pre-delivery ratio)
    total_balls = df['overs_limit'] * 6.0
    df['balls_remaining_ratio'] = (df['balls_remaining'] / total_balls.replace(0, 120.0)).clip(0.0, 1.0)
    df['wickets_ratio'] = (df['wickets_in_hand'] / 10.0).clip(0.0, 1.0)
    
    # Wicket Scarcity Index
    # As wickets fall, each remaining wicket becomes exponentially more scarce
    df['wicket_pressure_factor'] = (1.0 - df['wickets_ratio']) ** 1.5
    
    # Required vs Current Run Rate differential
    df['rate_deficit'] = np.maximum(0.0, df['rrr_clean'] - df['crr_clean'])
    
    return df

def get_training_dataset_1st_innings(df: pd.DataFrame, excluded_match_ids: set) -> pd.DataFrame:
    '''
    Prepares training dataset for the Historical Expected Remaining Runs model.
    Target = eventual innings total - pre-delivery score.
    Input features = strictly pre-delivery.
    '''
    # Filter to regular 1st innings, completed/valid matches
    mask = (
        (df['innings'] == 1) &
        (~df['match_id'].isin(excluded_match_ids)) &
        (df['overs_limit'] >= 19.0)
    )
    valid_df = df[mask].copy()
    
    # Eventual innings total is the sum of delivery runs for that innings
    actual_totals = valid_df.groupby('match_id')['total_delivery_runs'].sum().rename('eventual_innings_total')
    valid_df = valid_df.merge(actual_totals, on='match_id', how='left')
    
    # Target: remaining runs to be scored from this point forward
    valid_df['target_remaining_runs'] = valid_df['eventual_innings_total'] - valid_df['score_before']
    
    return valid_df
