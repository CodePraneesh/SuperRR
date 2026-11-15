# reliability.py
# Phase 3: Reliability, Bayesian Shrinkage, Confidence Tiers and Normalization.
from __future__ import annotations
import numpy as np
import pandas as pd

def apply_bayesian_shrinkage(raw_metric: pd.Series, sample_sizes: pd.Series, m_prior_weight: float = 60.0) -> pd.Series:
    pop_mean = raw_metric.mean()
    shrunk = (sample_sizes * raw_metric + m_prior_weight * pop_mean) / (sample_sizes + m_prior_weight)
    return shrunk

def calculate_reliability_confidence(sample_sizes: pd.Series, n_threshold: float = 150.0) -> pd.Series:
    return 100.0 * (1.0 - np.exp(-sample_sizes / n_threshold))

def assign_confidence_tier(sample_sizes: pd.Series, high_thresh: int = 150, mod_thresh: int = 60) -> pd.Series:
    tiers = np.where(sample_sizes >= high_thresh, 'High Confidence',
            np.where(sample_sizes >= mod_thresh, 'Moderate Confidence', 'Low Confidence'))
    return pd.Series(tiers, index=sample_sizes.index)

def min_max_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(50.0, index=series.index)
    scaled = 100.0 * (series - s_min) / (s_max - s_min)
    if invert:
        scaled = 100.0 - scaled
    return scaled.clip(0.0, 100.0)
