#!/usr/bin/env python3
'''
expected_batting.py
Phase 2B: Context-Based Neutral Expectation Models for Batting.
Predicts expected batter runs and dismissal probability per delivery.
Strictly relies on pre-delivery contextual features without player identity.
'''
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

BATTING_FEATURE_COLS = [
    'pressure_score',
    'score_before',
    'wickets_lost_before',
    'balls_remaining',
    'wickets_in_hand',
    'crr_clean',
    'is_powerplay',
    'is_middle',
    'is_death',
    'innings',
    'is_ipl',
    'rrr_clean',
    'runs_req_clean'
]

def prepare_batting_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Extracts and normalizes features strictly available before the delivery.
    '''
    d = df.copy()
    d['is_ipl'] = (d['competition_scope'] == 'IPL').astype(int)
    d['rrr_clean'] = d['required_run_rate'].fillna(0.0).clip(0.0, 36.0)
    d['runs_req_clean'] = d['runs_required'].fillna(0.0).clip(lower=0.0)
    d['crr_clean'] = d['current_run_rate'].fillna(8.0).clip(0.0, 36.0)
    return d

class BatterExpectedRunsModel:
    '''
    Predicts expected batter runs on a delivery given match context.
    '''
    def __init__(self, random_state: int = 42):
        self.model = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.05,
            max_depth=5,
            min_samples_leaf=30,
            l2_regularization=1.0,
            random_state=random_state
        )
        self.feature_cols = BATTING_FEATURE_COLS
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['batter_runs']
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

class BatterDismissalModel:
    '''
    Predicts striker dismissal probability on a delivery given match context.
    '''
    def __init__(self, random_state: int = 42):
        self.model = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.04,
            max_depth=4,
            min_samples_leaf=40,
            l2_regularization=2.0,
            random_state=random_state
        )
        self.feature_cols = BATTING_FEATURE_COLS
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        # Striker dismissal: player dismissed equals striker
        y = (train_df['dismissed_player_id'] == train_df['striker_id']).astype(int)
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)
