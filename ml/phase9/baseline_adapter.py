#!/usr/bin/env python3
"""
baseline_adapter.py
Phase 9: Statistical Baseline Model Adapter.
Exposes Phase 2B HistGradientBoosting expectation models for batting and bowling,
ensuring strict parity in training data, features, and target definitions.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

CORE_FEATURE_COLS = [
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

EXTENDED_FEATURE_COLS = CORE_FEATURE_COLS + [
    'target_clean',
    'balls_remaining_ratio',
    'wickets_ratio',
    'format_par_score'
]

def prepare_modeling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts and standardizes pre-delivery features.
    Strictly forbids post-delivery outcomes or future information.
    """
    d = df.copy()
    d['is_ipl'] = (d['competition_scope'] == 'IPL').astype(int)
    d['rrr_clean'] = d['required_run_rate'].fillna(0.0).clip(0.0, 36.0)
    d['runs_req_clean'] = d['runs_required'].fillna(0.0).clip(lower=0.0)
    d['crr_clean'] = d['current_run_rate'].fillna(8.0).clip(0.0, 36.0)
    d['target_clean'] = d['target_runs'].fillna(0.0).clip(lower=0.0)
    d['balls_remaining_ratio'] = (d['balls_remaining'] / 120.0).clip(0.0, 1.0)
    d['wickets_ratio'] = (d['wickets_in_hand'] / 10.0).clip(0.0, 1.0)
    d['format_par_score'] = d['format_par_score'].fillna(160.0)
    return d

class BaselineBatterRunsModel:
    """Statistical Baseline (HistGradientBoosting) for Batter Expected Runs."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.05,
            max_depth=5,
            min_samples_leaf=30,
            l2_regularization=1.0,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['batter_runs']
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

class BaselineBatterDismissalModel:
    """Statistical Baseline (HistGradientBoosting) for Striker Dismissal Probability."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.04,
            max_depth=4,
            min_samples_leaf=40,
            l2_regularization=2.0,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = (train_df['dismissed_player_id'] == train_df['striker_id']).astype(int)
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)

class BaselineBowlerRunsModel:
    """Statistical Baseline (HistGradientBoosting) for Bowler Runs Conceded."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.05,
            max_depth=5,
            min_samples_leaf=30,
            l2_regularization=1.0,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['bowler_runs_conceded']
        self.model.fit(X, y)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

class BaselineBowlerWicketModel:
    """Statistical Baseline (HistGradientBoosting) for Bowler Credited Wicket Probability."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.04,
            max_depth=4,
            min_samples_leaf=40,
            l2_regularization=2.0,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame):
        X = train_df[self.feature_cols]
        y = train_df['bowler_wicket'].astype(int)
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)
