#!/usr/bin/env python3
"""
catboost_experiment.py
Phase 9: CatBoost Experimental Expectation Models for Batting and Bowling.
Utilizes symmetric oblivious trees with native handling of numerical splits,
early stopping on the chronological validation set, and L2 leaf regularization.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, CatBoostClassifier

from ml.phase9.baseline_adapter import CORE_FEATURE_COLS, EXTENDED_FEATURE_COLS

class CatBoostBatterRunsModel:
    """CatBoost Regressor for Batter Expected Runs."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None, iterations: int = 250):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = CatBoostRegressor(
            iterations=iterations,
            learning_rate=0.05,
            depth=6,
            l2_leaf_reg=3.0,
            loss_function='RMSE',
            random_seed=random_state,
            verbose=False
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        X_train = train_df[self.feature_cols]
        y_train = train_df['batter_runs']
        eval_set = None
        if val_df is not None:
            eval_set = (val_df[self.feature_cols], val_df['batter_runs'])
        self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=25, verbose=False)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def get_feature_importance(self) -> dict[str, float]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        imp = self.model.get_feature_importance()
        return dict(zip(self.feature_cols, [float(x) for x in imp]))

    def save(self, filepath: str | Path):
        self.model.save_model(str(filepath))

    def load(self, filepath: str | Path):
        self.model.load_model(str(filepath))
        self.is_fitted = True

class CatBoostBatterDismissalModel:
    """CatBoost Classifier for Striker Dismissal Probability."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None, iterations: int = 200):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = CatBoostClassifier(
            iterations=iterations,
            learning_rate=0.04,
            depth=5,
            l2_leaf_reg=4.0,
            loss_function='Logloss',
            random_seed=random_state,
            verbose=False
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        X_train = train_df[self.feature_cols]
        y_train = (train_df['dismissed_player_id'] == train_df['striker_id']).astype(int)
        eval_set = None
        if val_df is not None:
            eval_set = (val_df[self.feature_cols], (val_df['dismissed_player_id'] == val_df['striker_id']).astype(int))
        self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=20, verbose=False)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)

    def get_feature_importance(self) -> dict[str, float]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        imp = self.model.get_feature_importance()
        return dict(zip(self.feature_cols, [float(x) for x in imp]))

    def save(self, filepath: str | Path):
        self.model.save_model(str(filepath))

    def load(self, filepath: str | Path):
        self.model.load_model(str(filepath))
        self.is_fitted = True

class CatBoostBowlerRunsModel:
    """CatBoost Regressor for Bowler Expected Runs Conceded."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None, iterations: int = 250):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = CatBoostRegressor(
            iterations=iterations,
            learning_rate=0.05,
            depth=6,
            l2_leaf_reg=3.0,
            loss_function='RMSE',
            random_seed=random_state,
            verbose=False
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        X_train = train_df[self.feature_cols]
        y_train = train_df['bowler_runs_conceded']
        eval_set = None
        if val_df is not None:
            eval_set = (val_df[self.feature_cols], val_df['bowler_runs_conceded'])
        self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=25, verbose=False)
        self.is_fitted = True

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)

    def get_feature_importance(self) -> dict[str, float]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        imp = self.model.get_feature_importance()
        return dict(zip(self.feature_cols, [float(x) for x in imp]))

    def save(self, filepath: str | Path):
        self.model.save_model(str(filepath))

    def load(self, filepath: str | Path):
        self.model.load_model(str(filepath))
        self.is_fitted = True

class CatBoostBowlerWicketModel:
    """CatBoost Classifier for Bowler Credited Wicket Probability."""
    def __init__(self, random_state: int = 42, feature_cols: list[str] = None, iterations: int = 200):
        self.feature_cols = feature_cols or CORE_FEATURE_COLS
        self.model = CatBoostClassifier(
            iterations=iterations,
            learning_rate=0.04,
            depth=5,
            l2_leaf_reg=4.0,
            loss_function='Logloss',
            random_seed=random_state,
            verbose=False
        )
        self.is_fitted = False

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None):
        X_train = train_df[self.feature_cols]
        y_train = train_df['bowler_wicket'].astype(int)
        eval_set = None
        if val_df is not None:
            eval_set = (val_df[self.feature_cols], val_df['bowler_wicket'].astype(int))
        self.model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=20, verbose=False)
        self.is_fitted = True

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        X = df[self.feature_cols]
        probs = self.model.predict_proba(X)[:, 1]
        return np.clip(probs, 0.001, 0.999)

    def get_feature_importance(self) -> dict[str, float]:
        if not self.is_fitted:
            raise ValueError("Model not fitted.")
        imp = self.model.get_feature_importance()
        return dict(zip(self.feature_cols, [float(x) for x in imp]))

    def save(self, filepath: str | Path):
        self.model.save_model(str(filepath))

    def load(self, filepath: str | Path):
        self.model.load_model(str(filepath))
        self.is_fitted = True
