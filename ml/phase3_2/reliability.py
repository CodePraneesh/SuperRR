# ml/phase3_2/reliability.py
# Phase 3.2: Refined Reliability, Robust Normalization, and Strict Sample Eligibility.
from __future__ import annotations
import numpy as np
import pandas as pd

def apply_bayesian_shrinkage(raw_metric: pd.Series, sample_sizes: pd.Series, m_prior_weight: float = 40.0) -> pd.Series:
    """
    Empirical Bayes shrinkage towards population mean:
    shrunk = (N * raw + M * pop_mean) / (N + M)
    """
    pop_mean = raw_metric.mean()
    shrunk = (sample_sizes * raw_metric + m_prior_weight * pop_mean) / (sample_sizes + m_prior_weight)
    return shrunk

def calculate_pressure_reliability(
    p_balls: pd.Series,
    p_matches: pd.Series,
    n_pball_scale: float = 60.0,
    n_pmatch_scale: float = 5.0
) -> pd.Series:
    """
    Pressure-specific reliability reflecting delivery depth and match dispersion:
    R_pressure = 100 * (1 - exp(-p_balls / n_pball_scale)) * (1 - exp(-p_matches / n_pmatch_scale))
    """
    ball_factor = 1.0 - np.exp(-p_balls / n_pball_scale)
    match_factor = 1.0 - np.exp(-p_matches / n_pmatch_scale)
    rel = 100.0 * (ball_factor * match_factor)
    return rel.clip(0.0, 100.0)

def min_max_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Standard Min-Max normalization mapping [min, max] to [0, 100].
    """
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(50.0, index=series.index)
    scaled = 100.0 * (series - s_min) / (s_max - s_min)
    if invert:
        scaled = 100.0 - scaled
    return scaled.clip(0.0, 100.0)

def robust_sigmoid_normalize(series: pd.Series, k: float = 0.6) -> pd.Series:
    """
    Robust Sigmoid Normalization to prevent extreme tail saturation:
    Z = (x - median) / (IQR / 1.349)
    Score = 100 / (1 + exp(-k * Z))
    Smoothly maps the median to 50.0, prevents extreme outliers from compressing
    the core distribution, and ensures strict monotonic differentiation.
    """
    med = series.median()
    iqr = np.percentile(series, 75) - np.percentile(series, 25)
    scale = iqr / 1.349 if iqr > 0 else (series.std() if series.std() > 0 else 1.0)
    z = (series - med) / scale
    score = 100.0 / (1.0 + np.exp(-z * k))
    return pd.Series(score, index=series.index).clip(0.0, 100.0)

def assign_batter_eligibility_tier(
    total_balls: pd.Series,
    pressure_balls: pd.Series,
    pressure_matches: pd.Series,
    high_pball: int = 100,
    high_pmatch: int = 8,
    high_totball: int = 150,
    mod_pball: int = 40,
    mod_pmatch: int = 3,
    mod_totball: int = 60
) -> pd.Series:
    """
    Assigns statistically defensible confidence tiers for official batter rankings:
    - High Confidence (Official Top 10 Eligible):
        pressure_deliveries >= 100 AND pressure_matches >= 8 AND total_deliveries >= 150
    - Moderate Confidence:
        pressure_deliveries >= 40 AND pressure_matches >= 3 AND total_deliveries >= 60
    - Low Confidence:
        All remaining batters.
    """
    is_high = (pressure_balls >= high_pball) & (pressure_matches >= high_pmatch) & (total_balls >= high_totball)
    is_mod = (pressure_balls >= mod_pball) & (pressure_matches >= mod_pmatch) & (total_balls >= mod_totball)
    
    tiers = np.where(is_high, 'High Confidence',
            np.where(is_mod, 'Moderate Confidence', 'Low Confidence'))
    return pd.Series(tiers, index=total_balls.index)
