# ml/phase3_3/confidence_system.py
# Phase 3.3: Unified Pressure-Specific Confidence & Sample Reliability System
from __future__ import annotations
import numpy as np
import pandas as pd

def calculate_effective_sample_size(p_balls: pd.Series, p_matches: pd.Series, icc: float = 0.15) -> pd.Series:
    """
    Calculates design-effect adjusted effective sample size accounting for match clustering:
    DEFF = 1 + (m_bar - 1) * rho
    N_eff = N_p / DEFF
    where m_bar = N_p / M_p and rho is intra-class correlation (default 0.15).
    """
    m_bar = p_balls / np.maximum(1, p_matches)
    deff = 1.0 + np.maximum(0.0, m_bar - 1.0) * icc
    n_eff = p_balls / deff
    return n_eff.round(2)

def calculate_pressure_uncertainty(match_std: pd.Series, p_matches: pd.Series) -> pd.Series:
    """
    Calculates standard error of the mean pressure match performance:
    SE = sigma_match / sqrt(M_p)
    """
    se = match_std / np.sqrt(np.maximum(1, p_matches))
    return se.round(2)

def assess_nonpressure_adequacy(np_balls: pd.Series, threshold: float = 60.0) -> pd.Series:
    """
    Evaluates adequacy of non-pressure sample for forming an unbiased adaptability baseline.
    Returns adequacy ratio in [0.0, 1.0].
    """
    ratio = (np_balls / threshold).clip(0.0, 1.0)
    return ratio.round(3)

def assign_batter_confidence_tier_33(
    total_balls: pd.Series,
    pressure_balls: pd.Series,
    pressure_matches: pd.Series,
    nonpressure_balls: pd.Series
) -> pd.Series:
    """
    Phase 3.3 Batter Confidence Rules:
    - High Confidence (Official Top 10 Eligible):
        pressure_balls >= 100 AND pressure_matches >= 8 AND total_balls >= 150 AND nonpressure_balls >= 40
    - Moderate Confidence:
        pressure_balls >= 40 AND pressure_matches >= 3 AND total_balls >= 60
    - Low Confidence:
        All remaining batters.
    """
    is_high = (pressure_balls >= 100) & (pressure_matches >= 8) & (total_balls >= 150) & (nonpressure_balls >= 40)
    is_mod = (pressure_balls >= 40) & (pressure_matches >= 3) & (total_balls >= 60)
    
    tiers = np.where(is_high, 'High Confidence',
            np.where(is_mod, 'Moderate Confidence', 'Low Confidence'))
    return pd.Series(tiers, index=total_balls.index)

def assign_bowler_confidence_tier_33(
    total_balls: pd.Series,
    pressure_balls: pd.Series,
    pressure_matches: pd.Series,
    balls_per_match: pd.Series
) -> pd.Series:
    """
    Phase 3.3 Bowler Confidence Rules (Workload-based, Role-neutral):
    - High Confidence (Official Top 10 Eligible):
        pressure_balls >= 100 AND pressure_matches >= 8 AND total_balls >= 180 (30 overs) AND balls_per_match >= 12.0
    - Moderate Confidence (Provisional):
        pressure_balls >= 40 AND pressure_matches >= 3 AND total_balls >= 60
    - Low Confidence (Part-Time / Small Sample):
        All remaining bowlers.
    """
    is_high = (pressure_balls >= 100) & (pressure_matches >= 8) & (total_balls >= 180) & (balls_per_match >= 12.0)
    is_mod = (pressure_balls >= 40) & (pressure_matches >= 3) & (total_balls >= 60)
    
    tiers = np.where(is_high, 'High Confidence',
            np.where(is_mod, 'Moderate Confidence', 'Low Confidence'))
    return pd.Series(tiers, index=total_balls.index)
