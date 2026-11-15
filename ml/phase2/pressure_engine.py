#!/usr/bin/env python3
'''
pressure_engine.py
SupeRR Intelligence Phase 2A: Dynamic Pressure Detection Engine.
Calculates normalized Contextual Pressure Index (0-100) per delivery using strictly pre-ball information.
'''
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from ml.phase2.pressure_features import extract_predelivery_features, get_training_dataset_1st_innings

class FirstInningsExpectedRunsModel:
    '''
    Historical Expected Remaining Runs Model for 1st Innings.
    Trained strictly on pre-delivery states to predict remaining runs.
    '''
    def __init__(self):
        self.model = HistGradientBoostingRegressor(
            max_iter=120,
            learning_rate=0.08,
            max_depth=6,
            min_samples_leaf=25,
            random_state=42
        )
        self.feature_cols = [
            'balls_remaining', 'wickets_in_hand', 'score_before',
            'crr_clean', 'is_powerplay', 'is_death'
        ]
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['target_remaining_runs']
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model must be fitted before predict.')
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)


class DynamicPressureEngine:
    '''
    Core Pressure Detection Engine that computes normalized 0-100 pressure indices.
    '''
    def __init__(self):
        self.exp_runs_model = FirstInningsExpectedRunsModel()
        self.par_score_ipl = 186.0
        self.par_score_t20i = 171.0

    def fit_first_innings_model(self, df: pd.DataFrame, excluded_matches: set):
        '''
        Fits the expected remaining runs model on historical 1st innings data.
        '''
        train_data = get_training_dataset_1st_innings(df, excluded_matches)
        self.exp_runs_model.fit(train_data)

    def calculate_first_innings_pressure(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Calculates 1st innings pressure score (0-100).
        Evaluates:
        - Expected remaining runs & projected final total vs format par
        - Wickets in hand and scarcity penalty
        - Phase urgency (accelerating into death overs)
        - Deficit against projected par
        '''
        d = df.copy()
        pred_remaining = self.exp_runs_model.predict(d)
        d['expected_remaining_runs'] = pred_remaining
        d['expected_final_total'] = d['score_before'] + d['expected_remaining_runs']
        
        # Format-specific benchmark par
        format_par = np.where(d['competition_scope'].eq('IPL'), self.par_score_ipl, self.par_score_t20i)
        d['format_par_score'] = format_par
        
        # Par Deficit Ratio: how far below benchmark par is the current projection?
        # A projection of 140 when par is 186 gives high pressure; 220 gives low pressure
        par_deficit = np.maximum(0.0, format_par - d['expected_final_total'])
        par_pressure = (par_deficit / 50.0).clip(0.0, 1.0)
        
        # Wicket Scarcity Factor: as wickets fall, pressure multiplies
        # e.g., 8 wkts in hand = 0.04; 3 wkts in hand = 0.58; 1 wkt in hand = 0.85
        wicket_pressure = (d['wicket_pressure_factor']).clip(0.0, 1.0)
        
        # Phase Urgency: overs elapsed increases pressure (especially in death overs)
        balls_used = 120.0 - d['balls_remaining']
        time_urgency = (balls_used / 120.0).clip(0.0, 1.0)
        
        # Run-Rate Drag: penalty if current run rate is sluggish (< 7.5 rpo)
        rr_drag = np.maximum(0.0, (8.5 - d['crr_clean']) / 8.5).clip(0.0, 1.0)
        
        # Composite First-Innings Pressure Raw Score (0 to 1)
        raw_p1 = (
            0.35 * par_pressure +
            0.35 * wicket_pressure +
            0.20 * (time_urgency * (0.6 + 0.4 * d['is_death'])) +
            0.10 * rr_drag
        )
        
        # Calibrated Sigmoid Normalization to 0-100
        # Maps raw_p1 to [0, 100] distribution with median around 45-50
        scaled_p1 = 100.0 / (1.0 + np.exp(-6.5 * (raw_p1 - 0.42)))
        d['first_innings_pressure_score'] = scaled_p1.clip(0.0, 100.0)
        return d

    def calculate_second_innings_pressure(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Calculates Chasing Pressure Score (0-100).
        Evaluates:
        - Required run rate (steep exponential escalation beyond 10-12 RPO)
        - Balls remaining & run-chase leverage
        - Wickets in hand relative to runs required
        - Rate deficit (RRR - CRR)
        '''
        d = df.copy()
        
        # Required Run Rate Component:
        # 6.0 RPO -> mild (0.2); 10.0 RPO -> high (0.6); 15.0 RPO -> critical (0.95)
        rrr = d['rrr_clean']
        rrr_factor = (rrr / 14.0).clip(0.0, 1.5) ** 1.3
        rrr_component = np.tanh(rrr_factor).clip(0.0, 1.0)
        
        # Resource Ratio: Balls available per run required vs ideal (1.33 balls per run = 4.5 RPO)
        # When balls_per_run < 0.6, pressure spikes
        runs_req = np.maximum(1.0, d['runs_req_clean'])
        balls_rem = d['balls_remaining']
        balls_per_run = (balls_rem / runs_req).clip(0.0, 2.5)
        resource_deficit = np.maximum(0.0, 1.0 - (balls_per_run / 1.0)).clip(0.0, 1.0)
        
        # Wickets Scarcity vs Runs Required:
        # e.g., 50 runs needed with 2 wickets in hand is extreme pressure
        runs_per_wicket_needed = (runs_req / np.maximum(1, d['wickets_in_hand'])).clip(0.0, 60.0)
        wkt_risk = (runs_per_wicket_needed / 30.0).clip(0.0, 1.0)
        
        # Closeness/Leverage multiplier: Final 5 overs (balls <= 30) intensify pressure
        death_leverage = np.where(balls_rem <= 30.0, 1.0 + (30.0 - balls_rem) / 60.0, 1.0)
        
        # Composite Raw Chase Pressure
        raw_p2 = (
            0.45 * rrr_component +
            0.30 * resource_deficit +
            0.25 * wkt_risk
        ) * death_leverage
        raw_p2 = raw_p2.clip(0.0, 1.5)
        
        # Calibrated Sigmoid Normalization to 0-100
        scaled_p2 = 100.0 / (1.0 + np.exp(-6.0 * (raw_p2 - 0.48)))
        d['chasing_pressure_score'] = scaled_p2.clip(0.0, 100.0)
        return d

    def score_deliveries(self, df: pd.DataFrame, excluded_matches: set) -> pd.DataFrame:
        '''
        End-to-end scoring pipeline for all deliveries.
        Distinguishes 1st and 2nd innings while keeping calculations distinguishable.
        '''
        print('Extracting pre-delivery features...')
        d = extract_predelivery_features(df)
        
        print('Fitting 1st innings expected runs model...')
        self.fit_first_innings_model(d, excluded_matches)
        
        print('Scoring 1st innings pressure...')
        d1 = d[d['innings'] == 1].copy()
        d1 = self.calculate_first_innings_pressure(d1)
        d1['chasing_pressure_score'] = np.nan
        d1['pressure_score'] = d1['first_innings_pressure_score']
        
        print('Scoring 2nd innings pressure...')
        d2 = d[d['innings'] == 2].copy()
        d2 = self.calculate_second_innings_pressure(d2)
        d2['expected_remaining_runs'] = np.nan
        d2['expected_final_total'] = np.nan
        d2['format_par_score'] = np.nan
        d2['first_innings_pressure_score'] = np.nan
        d2['pressure_score'] = d2['chasing_pressure_score']
        
        # Innings 3+ (Super Overs): Extreme pressure default (scored 85-95 based on wickets & balls)
        d3 = d[d['innings'] >= 3].copy()
        if len(d3) > 0:
            d3['expected_remaining_runs'] = np.nan
            d3['expected_final_total'] = np.nan
            d3['format_par_score'] = np.nan
            d3['first_innings_pressure_score'] = np.nan
            d3['chasing_pressure_score'] = 90.0 + (10 - d3['wickets_in_hand']).clip(0, 10)
            d3['pressure_score'] = d3['chasing_pressure_score'].clip(0.0, 100.0)
            
        scored = pd.concat([d1, d2, d3], ignore_index=True)
        scored = scored.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)
        
        # Pressure Tier Categorization (Scientific Quintiles/Tiers)
        scored['pressure_tier'] = pd.cut(
            scored['pressure_score'],
            bins=[-0.1, 25.0, 50.0, 75.0, 90.0, 100.0],
            labels=['Low', 'Moderate', 'High', 'Very High', 'Extreme']
        )
        
        return scored
