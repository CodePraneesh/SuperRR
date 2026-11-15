# ml/phase3_1/reliability.py
# Phase 3.1: Refined Reliability, Pressure-Specific Confidence, and Eligibility Tiers.
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
    At p_balls = 60 and p_matches = 5: (1 - 1/e) * (1 - 1/e) ≈ 0.632 * 0.632 = 40.0
    At p_balls = 150 and p_matches = 15: (1 - 0.082) * (1 - 0.05) ≈ 0.87 * 100 = 87.0
    """
    ball_factor = 1.0 - np.exp(-p_balls / n_pball_scale)
    match_factor = 1.0 - np.exp(-p_matches / n_pmatch_scale)
    rel = 100.0 * (ball_factor * match_factor)
    return rel.clip(0.0, 100.0)

def assign_pressure_confidence_tier(
    total_balls: pd.Series,
    pressure_balls: pd.Series,
    pressure_matches: pd.Series,
    high_pball: int = 50,
    high_pmatch: int = 3,
    mod_pball: int = 20,
    mod_pmatch: int = 2
) -> pd.Series:
    """
    Assigns confidence tiers based on joint pressure-specific sample criteria:
    - High Confidence: pressure_balls >= 50 AND pressure_matches >= 3 (AND total_balls >= 100)
    - Moderate Confidence: pressure_balls >= 20 AND pressure_matches >= 2 (AND total_balls >= 40)
    - Low Confidence: all other players
    """
    is_high = (pressure_balls >= high_pball) & (pressure_matches >= high_pmatch) & (total_balls >= 100)
    is_mod = (pressure_balls >= mod_pball) & (pressure_matches >= mod_pmatch) & (total_balls >= 40)
    
    tiers = np.where(is_high, 'High Confidence',
            np.where(is_mod, 'Moderate Confidence', 'Low Confidence'))
    return pd.Series(tiers, index=total_balls.index)

def min_max_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(50.0, index=series.index)
    scaled = 100.0 * (series - s_min) / (s_max - s_min)
    if invert:
        scaled = 100.0 - scaled
    return scaled.clip(0.0, 100.0)
