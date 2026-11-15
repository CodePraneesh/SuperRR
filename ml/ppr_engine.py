"""
ml/ppr_engine.py
SupeRR Intelligence — Pressure Performance Reliability (PPR) & Volume-Adjusted CPRI Engine

Upgrades the CPRI ranking engine to prioritize players with substantial pressure-ball
exposure and proven successful clutch performance, preventing low-volume inflated rates
from dominating the headline leaderboard while preserving transparent raw CPRI scores.

Key Components:
1. EvidenceTierConfig: Configurable thresholds for sample-size evidence tiers.
2. Role-Specific Delivery Metrics: Computes true delivery-level pressure success rates,
   boundary percentages, dot percentages, and performance relative to expected outcomes.
3. Pressure Performance Reliability (PPR): Non-arbitrary, statistically grounded metric
   combining role-specific success, cross-match consistency, and sample-size credibility.
4. Volume-Adjusted CPRI (Adjusted CPRI): Empirical Bayes shrinkage on small samples
   coupled with PPR, guaranteeing that high volume with sustained success is rewarded
   and high volume with poor performance is never elevated.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd


@dataclass
class EvidenceTierConfig:
    """
    Configurable sample size classification thresholds based on pressure deliveries.
    Default standards:
    - Elite Evidence: 600+ pressure balls
    - Strong Evidence: 400–599 pressure balls
    - Moderate Evidence: 250–399 pressure balls
    - Limited Evidence: 150–249 pressure balls
    - Insufficient Evidence: Below 150 pressure balls
    """
    elite_threshold: int = 600
    strong_threshold: int = 400
    moderate_threshold: int = 250
    limited_threshold: int = 150

    def classify(self, pressure_deliveries: int) -> str:
        """Classify player into an evidence tier based on pressure deliveries."""
        n = int(pressure_deliveries)
        if n >= self.elite_threshold:
            return "Elite Evidence"
        elif n >= self.strong_threshold:
            return "Strong Evidence"
        elif n >= self.moderate_threshold:
            return "Moderate Evidence"
        elif n >= self.limited_threshold:
            return "Limited Evidence"
        else:
            return "Insufficient Evidence"

    def is_main_eligible(self, pressure_deliveries: int) -> bool:
        """Main Leaderboard requires at least Strong Evidence (>= 400 balls)."""
        return int(pressure_deliveries) >= self.strong_threshold

    def get_eligibility_status(self, pressure_deliveries: int) -> str:
        """Return human-readable eligibility category."""
        n = int(pressure_deliveries)
        if n >= self.strong_threshold:
            return "Main Leaderboard"
        elif n >= self.limited_threshold:
            return "Contender / Emerging"
        else:
            return "Insufficient Evidence"


DEFAULT_EVIDENCE_CONFIG = EvidenceTierConfig()


# =============================================================================
# Role-Specific Granular Delivery Metrics
# =============================================================================

def compute_batter_role_metrics(
    deliveries_df: pd.DataFrame,
    pressure_threshold: float = 50.0
) -> pd.DataFrame:
    """
    Aggregates delivery expectations for batters under pressure.
    A batter delivery is deemed 'successful' under pressure if:
    1. A boundary was scored (runs >= 4), OR
    2. Runs scored exceeded expectations for that ball (batting_run_residual > 0).
    """
    p_balls = deliveries_df[deliveries_df["pressure_score"] >= pressure_threshold].copy()
    
    # Successful delivery flag
    p_balls["is_boundary"] = p_balls["actual_batter_runs"].isin([4, 6])
    p_balls["is_dot"] = p_balls["actual_batter_runs"] == 0
    p_balls["is_success"] = p_balls["is_boundary"] | (p_balls["batting_run_residual"] > 0)

    grouped = p_balls.groupby("striker_id").agg(
        p_deliveries=("actual_batter_runs", "count"),
        p_runs=("actual_batter_runs", "sum"),
        p_dots=("is_dot", "sum"),
        p_boundaries=("is_boundary", "sum"),
        p_outs=("actual_dismissal_outcome", "sum"),
        p_successes=("is_success", "sum"),
        exp_runs=("expected_batter_runs", "sum"),
        exp_outs=("expected_dismissal_prob", "sum"),
        total_run_res=("batting_run_residual", "sum"),
        total_surv_res=("batting_dismissal_residual", "sum"),
    ).reset_index()

    grouped["dot_pct"] = (grouped["p_dots"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["boundary_pct"] = (grouped["p_boundaries"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["dismissal_freq_pct"] = (grouped["p_outs"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["strike_rate"] = (grouped["p_runs"] / (grouped["p_deliveries"] / 100.0)).round(2)
    grouped["success_rate_pct"] = (grouped["p_successes"] / grouped["p_deliveries"] * 100.0).round(2)

    return grouped


def compute_bowler_role_metrics(
    deliveries_df: pd.DataFrame,
    pressure_threshold: float = 50.0
) -> pd.DataFrame:
    """
    Aggregates delivery expectations for bowlers under pressure.
    A bowler delivery is deemed 'successful' under pressure if:
    1. A dot ball was bowled (runs_conceded == 0), OR
    2. A wicket was taken (actual_wicket_outcome == 1), OR
    3. Runs conceded were strictly below expectation (bowling_run_residual < 0).
    """
    p_balls = deliveries_df[deliveries_df["pressure_score"] >= pressure_threshold].copy()

    p_balls["is_dot"] = p_balls["actual_runs_conceded"] == 0
    p_balls["is_boundary_conceded"] = p_balls["actual_runs_conceded"].isin([4, 6])
    p_balls["is_wicket"] = p_balls["actual_wicket_outcome"] == 1
    p_balls["is_success"] = p_balls["is_dot"] | p_balls["is_wicket"] | (p_balls["bowling_run_residual"] < 0)

    grouped = p_balls.groupby("bowler_id").agg(
        p_deliveries=("actual_runs_conceded", "count"),
        p_runs_conceded=("actual_runs_conceded", "sum"),
        p_dots=("is_dot", "sum"),
        p_boundaries_conceded=("is_boundary_conceded", "sum"),
        p_wickets=("is_wicket", "sum"),
        p_successes=("is_success", "sum"),
        exp_runs_conceded=("expected_runs_conceded", "sum"),
        exp_wickets=("expected_wicket_prob", "sum"),
        total_runs_saved=("bowling_run_residual", lambda s: float(-s.sum())),
        total_wkts_above_exp=("bowling_wicket_residual", "sum"),
    ).reset_index()

    grouped["dot_pct"] = (grouped["p_dots"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["boundary_conceded_pct"] = (grouped["p_boundaries_conceded"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["wicket_freq_pct"] = (grouped["p_wickets"] / grouped["p_deliveries"] * 100.0).round(2)
    grouped["economy"] = (grouped["p_runs_conceded"] / (grouped["p_deliveries"] / 6.0)).round(2)
    grouped["success_rate_pct"] = (grouped["p_successes"] / grouped["p_deliveries"] * 100.0).round(2)

    return grouped


# =============================================================================
# Pressure Performance Reliability (PPR) Formulation
# =============================================================================

def calculate_role_success_norm(
    success_rate_pct: float,
    role: str
) -> float:
    """
    Normalizes role-appropriate success rate percentage onto a standard [0, 100] scale.
    - Batters: league median ~30.0%, std ~6.0% (successful attacking deliveries)
    - Bowlers: league median ~60.0%, std ~8.0% (dots, wickets, and run suppression)
    """
    if role.lower() == "batter":
        z = (float(success_rate_pct) - 30.0) / 6.0
    else:
        z = (float(success_rate_pct) - 60.0) / 8.0
    
    score = 50.0 + z * 15.0
    return float(np.clip(score, 0.0, 100.0))


def calculate_ppr(
    pressure_deliveries: int,
    score_pressure_impact: float,
    score_adaptability: float,
    score_consistency: float,
    success_rate_pct: float,
    role: str,
    n_prior: float = 250.0
) -> float:
    """
    Calculates Pressure Performance Reliability (PPR) [0 - 100].
    
    PPR considers:
    1. Role-specific successful outcomes under pressure (normalized success rate).
    2. Performance relative to expected outcomes (pressure impact score).
    3. Performance consistency across matches (clutch consistency score).
    4. Tactical adaptability under pressure.
    5. Sample-size Bayesian credibility: lambda(N) = N / (N + n_prior).
    
    Mathematical Properties:
    - Zero exposure regresses to neutral baseline (50.0).
    - Substandard performance (CQI < 50.0) stays below 50.0 regardless of volume.
      High volume never compensates for poor clutch execution.
    - High-volume elite execution (CQI > 70.0, N >= 600) approaches true full credit (>68-75).
    """
    n = max(0, int(pressure_deliveries))
    s_norm = calculate_role_success_norm(success_rate_pct, role)
    
    # Clutch Quality Index (pure skill under pressure)
    cqi = (
        0.35 * float(score_pressure_impact) +
        0.25 * float(score_adaptability) +
        0.20 * float(score_consistency) +
        0.20 * s_norm
    )
    
    # Bayesian credibility shrinkage factor
    credibility = n / (n + n_prior)
    
    ppr = 50.0 + (cqi - 50.0) * credibility
    return round(float(np.clip(ppr, 0.0, 100.0)), 2)


# =============================================================================
# Volume-Adjusted CPRI (Adjusted CPRI) Formulation
# =============================================================================

def calculate_adjusted_cpri(
    pressure_deliveries: int,
    score_pressure_impact: float,
    score_adaptability: float,
    score_consistency: float,
    score_reliability: float,
    ppr_score: float,
    n_shrink_prior: float = 150.0
) -> float:
    """
    Calculates Volume-Adjusted CPRI.
    
    Requirements Enforced:
    1. Preserves original raw CPRI for complete transparency.
    2. Calculates volume-adjusted score separately.
    3. Proportionately regresses small samples using empirical Bayes shrinkage
       on the skill components (Impact, Adaptability, Consistency) toward the population prior (50.0).
    4. Incorporates PPR to reward sustained high-volume execution.
    5. Prevents double-counting: Reliability Confidence (RC) is weighted at 20%,
       shrunk skill at 60%, and PPR at 20%.
    6. Ensures high volume never compensates for poor performance:
       If a player's skill is below 50.0, shrinking pulls them toward 50.0,
       and their PPR is below 50.0, keeping them safely below top ranks.
    """
    n = max(0, int(pressure_deliveries))
    
    # Unweighted raw clutch skill (PI: 40%, PA: 25%, CC: 20% scaled out of 0.85)
    skill_raw = (
        0.40 * float(score_pressure_impact) +
        0.25 * float(score_adaptability) +
        0.20 * float(score_consistency)
    ) / 0.85
    
    # Empirical Bayes shrinkage towards neutral population mean (50.0)
    shrink_factor = n / (n + n_shrink_prior)
    skill_shrunk = 50.0 + (skill_raw - 50.0) * shrink_factor
    
    # Composite Volume-Adjusted CPRI
    adj_cpri = (
        0.60 * skill_shrunk +
        0.20 * float(score_reliability) +
        0.20 * float(ppr_score)
    )
    
    return round(float(np.clip(adj_cpri, 0.0, 100.0)), 2)


# =============================================================================
# High-Level Player Enhancement
# =============================================================================

def enrich_player_with_ppr_and_adjustment(
    player_dict: Dict[str, Any],
    role: str,
    delivery_metrics: Optional[Dict[str, Any]] = None,
    config: Optional[EvidenceTierConfig] = None
) -> Dict[str, Any]:
    """
    Takes an official player or candidate dictionary and attaches:
    - evidence_tier: "Elite Evidence", "Strong Evidence", etc.
    - is_main_eligible: bool (True if N >= 400)
    - eligibility_status: "Main Leaderboard", "Contender / Emerging", "Insufficient Evidence"
    - success_rate_pct: float
    - role_success_metrics: granular stats dict
    - ppr_score: float
    - adjusted_cpri: float
    """
    cfg = config or DEFAULT_EVIDENCE_CONFIG
    p = dict(player_dict)
    
    p_stats = p.get("pressure_stats", {})
    p_balls = int(p_stats.get("pressure_deliveries", p.get("pressure_deliveries", 0)))
    
    # Evidence tier & eligibility
    p["evidence_tier"] = cfg.classify(p_balls)
    p["is_main_eligible"] = cfg.is_main_eligible(p_balls)
    p["eligibility_status"] = cfg.get_eligibility_status(p_balls)

    # Granular role metrics
    metrics = delivery_metrics or {}
    success_rate = float(metrics.get("success_rate_pct", 0.0))
    if success_rate == 0.0:
        # Fallback approximation from existing fields if delivery-level missing
        if role.lower() == "batter":
            sr = float(p_stats.get("pressure_strike_rate", 140.0))
            success_rate = round(float(np.clip(25.0 + (sr - 130.0) * 0.2, 10.0, 50.0)), 2)
        else:
            econ = float(p_stats.get("pressure_economy", 8.0))
            success_rate = round(float(np.clip(65.0 - (econ - 7.0) * 4.0, 30.0, 85.0)), 2)

    p["success_rate_pct"] = success_rate
    p["role_success_metrics"] = {
        "success_rate_pct": success_rate,
        "dot_pct": float(metrics.get("dot_pct", 0.0)),
        "boundary_pct": float(metrics.get("boundary_pct", metrics.get("boundary_conceded_pct", 0.0))),
        "frequency_metric_pct": float(metrics.get("dismissal_freq_pct", metrics.get("wicket_freq_pct", 0.0))),
    }

    # Components
    comps = p.get("components", {})
    pi = float(comps.get("pressure_impact", p.get("score_pressure_impact", 50.0)))
    pa = float(comps.get("pressure_adaptability", p.get("score_adaptability", 50.0)))
    cc = float(comps.get("clutch_consistency", p.get("score_consistency", 50.0)))
    rc = float(comps.get("reliability_confidence", p.get("score_reliability", 50.0)))

    # Compute PPR
    ppr = calculate_ppr(
        pressure_deliveries=p_balls,
        score_pressure_impact=pi,
        score_adaptability=pa,
        score_consistency=cc,
        success_rate_pct=success_rate,
        role=role
    )
    p["ppr_score"] = ppr

    # Compute Adjusted CPRI
    adj_cpri = calculate_adjusted_cpri(
        pressure_deliveries=p_balls,
        score_pressure_impact=pi,
        score_adaptability=pa,
        score_consistency=cc,
        score_reliability=rc,
        ppr_score=ppr
    )
    p["adjusted_cpri"] = adj_cpri

    return p
