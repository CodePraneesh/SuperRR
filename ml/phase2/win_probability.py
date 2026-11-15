#!/usr/bin/env python3
'''
win_probability.py
Phase 2C: Win Probability Models for 1st Innings and 2nd Innings (Chasing).
Uses LightGBM with pre-delivery contextual features and empirical calibration.
'''
from __future__ import annotations
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.calibration import CalibratedClassifierCV

CHASE_FEATURES = [
    'score_before', 'wickets_lost_before', 'balls_remaining',
    'wickets_in_hand', 'crr_clean', 'is_powerplay', 'is_middle', 'is_death',
    'is_ipl', 'rrr_clean', 'runs_req_clean', 'target_clean', 'pressure_score'
]

INN1_FEATURES = [
    'score_before', 'wickets_lost_before', 'balls_remaining',
    'wickets_in_hand', 'crr_clean', 'is_powerplay', 'is_middle', 'is_death',
    'is_ipl', 'expected_final_total', 'format_par_score', 'pressure_score'
]

def prepare_win_prob_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Prepares pre-delivery contextual features for win probability estimation.
    '''
    d = df.copy()
    d['is_ipl'] = (d['competition_scope'] == 'IPL').astype(int)
    d['rrr_clean'] = d['required_run_rate'].fillna(0.0).clip(0.0, 36.0)
    d['runs_req_clean'] = d['runs_required'].fillna(0.0).clip(lower=0.0)
    d['crr_clean'] = d['current_run_rate'].fillna(8.0).clip(0.0, 36.0)
    d['target_clean'] = d['target_runs'].fillna(0.0)
    d['format_par_score'] = np.where(d['is_ipl'] == 1, 186.0, 171.0)
    if 'expected_final_total' not in d.columns:
        d['expected_final_total'] = d['score_before'] + 8.0 * (d['balls_remaining'] / 6.0)
    return d

class ChasingWinProbabilityModel:
    '''
    Model estimating batting team win probability in 2nd innings (chasing).
    '''
    def __init__(self, random_state: int = 42):
        self.base_model = lgb.LGBMClassifier(
            n_estimators=160,
            learning_rate=0.04,
            num_leaves=31,
            max_depth=6,
            min_child_samples=30,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            verbose=-1
        )
        self.feature_cols = CHASE_FEATURES
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['batting_team_won']
        self.base_model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        
        # Check for terminal match states first
        # 1. Runs required <= 0: Win (1.0)
        # 2. Wickets in hand == 0 and runs required > 0: Loss (0.0)
        # 3. Balls remaining == 0 and runs required > 1: Loss (0.0)
        # 4. Balls remaining == 0 and runs required == 1: Tie (0.5)
        X = df[self.feature_cols]
        raw_probs = self.base_model.predict_proba(X)[:, 1]
        
        runs_req = df['runs_req_clean'].values
        wkts_left = df['wickets_in_hand'].values
        balls_rem = df['balls_remaining'].values
        
        probs = np.where(runs_req <= 0.0, 1.0,
                np.where(wkts_left <= 0, 0.0,
                np.where((balls_rem <= 0) & (runs_req > 1.0), 0.0,
                np.where((balls_rem <= 0) & (runs_req == 1.0), 0.5, raw_probs))))
                
        return np.clip(probs, 0.0, 1.0)

class FirstInningsWinProbabilityModel:
    '''
    Model estimating 1st innings batting team win probability based on projected par.
    '''
    def __init__(self, random_state: int = 42):
        self.base_model = lgb.LGBMClassifier(
            n_estimators=120,
            learning_rate=0.03,
            num_leaves=25,
            max_depth=5,
            min_child_samples=40,
            random_state=random_state,
            verbose=-1
        )
        self.feature_cols = INN1_FEATURES
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['batting_team_won']
        self.base_model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        X = df[self.feature_cols]
        probs = self.base_model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.01, 0.99)
