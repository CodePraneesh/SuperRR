#!/usr/bin/env python3
'''
performance_delta.py
Phase 2B: Actual vs Expected Performance Residuals and Pressure-Weighting.
Defines clear sign conventions and separates run impact from wicket impact.
'''
from __future__ import annotations
import numpy as np
import pandas as pd

def compute_batting_performance_residuals(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Computes delivery-level batting residuals:
    - batting_run_residual = actual_batter_runs - expected_batter_runs (positive = above expected)
    - batting_dismissal_residual = expected_dismissal_prob - actual_dismissed (positive = survived high-risk ball)
    - pressure_weight = 1.0 + (pressure_score / 100.0)
    - pressure_adjusted_run_delta = batting_run_residual * pressure_weight
    '''
    d = df.copy()
    
    # 1. Run Residual
    d['batting_run_residual'] = d['actual_batter_runs'] - d['expected_batter_runs']
    
    # 2. Dismissal Residual
    # If expected_prob is 0.20 and player was not dismissed (0), residual is +0.20 (good survival)
    # If dismissed (1), residual is 0.20 - 1.0 = -0.80 (negative impact)
    d['batting_dismissal_residual'] = d['expected_dismissal_prob'] - d['actual_dismissal_outcome']
    
    # 3. Pressure Weighting (Contextual Leverage multiplier)
    # Scales smoothly from 1.0 (zero pressure) to 2.0 (maximum 100 pressure)
    d['pressure_multiplier'] = 1.0 + (d['pressure_score'].clip(0.0, 100.0) / 100.0)
    d['pressure_adjusted_batting_run_delta'] = d['batting_run_residual'] * d['pressure_multiplier']
    d['pressure_adjusted_batting_out_delta'] = d['batting_dismissal_residual'] * d['pressure_multiplier']
    
    return d

def compute_bowling_performance_residuals(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Computes delivery-level bowling residuals:
    - bowling_run_residual = expected_runs_conceded - actual_runs_conceded (positive = conceded fewer runs than expected)
    - bowling_wicket_residual = actual_wicket_outcome - expected_wicket_prob (positive = took a wicket above expected)
    - pressure_weight = 1.0 + (pressure_score / 100.0)
    - pressure_adjusted_run_delta = bowling_run_residual * pressure_weight
    '''
    d = df.copy()
    
    # 1. Run Residual (REVERSED sign convention: expected minus actual)
    d['bowling_run_residual'] = d['expected_runs_conceded'] - d['actual_runs_conceded']
    
    # 2. Wicket Residual
    # If took wicket (1) and expected was 0.05, residual is +0.95 (great wicket)
    # If no wicket (0) and expected was 0.05, residual is -0.05
    d['bowling_wicket_residual'] = d['actual_wicket_outcome'] - d['expected_wicket_prob']
    
    # 3. Pressure Weighting
    d['pressure_multiplier'] = 1.0 + (d['pressure_score'].clip(0.0, 100.0) / 100.0)
    d['pressure_adjusted_bowling_run_delta'] = d['bowling_run_residual'] * d['pressure_multiplier']
    d['pressure_adjusted_bowling_wicket_delta'] = d['bowling_wicket_residual'] * d['pressure_multiplier']
    
    return d
