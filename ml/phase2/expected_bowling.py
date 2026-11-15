#!/usr/bin/env python3
'''
expected_bowling.py
Phase 2B: Context-Based Neutral Expectation Models for Bowling.
Predicts expected bowler runs conceded and legal credited wicket probability per delivery.
Strictly relies on pre-delivery contextual features without player identity.
'''
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

BOWLING_FEATURE_COLS = [
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

def prepare_bowling_features(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Extracts and normalizes features strictly available before the delivery for bowling.
    '''
    d = df.copy()
    d['is_ipl'] = (d['competition_scope'] == 'IPL').astype(int)
    d['rrr_clean'] = d['required_run_rate'].fillna(0.0).clip(0.0, 36.0)
    d['runs_req_clean'] = d['runs_required'].fillna(0.0).clip(lower=0.0)
    d['crr_clean'] = d['current_run_rate'].fillna(8.0).clip(0.0, 36.0)
    return d

class BowlerExpectedRunsModel:
    '''
    Predicts expected bowler runs conceded on a delivery given match context.
    Accounts for batter runs and bowler extras (wides/no-balls), excluding byes/leg-byes.
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
        self.feature_cols = BOWLING_FEATURE_COLS
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        # Bowler runs conceded as validated in Phase 1
        y = train_df['bowler_runs_conceded']
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

class BowlerWicketModel:
    '''
    Predicts legal bowler wicket probability on a delivery given match context.
    Only credits wickets credited to the bowler (Bowled, Caught, LBW, Stumped, Hit Wicket).
    Strictly excludes Run Out, Retired Out, Obstructing Field, and No-ball wickets.
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
        self.feature_cols = BOWLING_FEATURE_COLS
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        # bowler_wicket boolean from corrected Phase 1 / Task 3
        y = train_df['bowler_wicket'].astype(int)
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError('Model not fitted.')
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)
