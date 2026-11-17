"""
backend/app/schemas/official.py
Pydantic schemas for the authoritative official Phase 13 CPRI rankings (and supplementary Phase 8 baseline)
and High-Volume Pressure Performance Reliability (PPR) rankings.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.player import CPRIComponents


class RankUncertainty(BaseModel):
    rank_p5: int = Field(..., description="5th percentile bootstrap rank (upper bound)")
    rank_p95: int = Field(..., description="95th percentile bootstrap rank (lower bound)")
    median_rank: int = Field(..., description="Median bootstrap rank")
    rank_std: float = Field(..., description="Standard deviation of bootstrap ranks")
    top10_inclusion_freq: float = Field(..., description="Empirical frequency of top 10 inclusion across resamples")
    ci_display: str = Field(..., description="Formatted 90% confidence interval, e.g. '[1, 22]'")


class OfficialPlayerItem(BaseModel):
    official_rank: int = Field(..., description="Official frozen competition rank (1-10 for top 10, 11+ for candidates)")
    player_id: int = Field(..., description="Official numeric player ID")
    player_name: str = Field(..., description="Full canonical player name")
    role: str = Field(..., description="Player role: 'Batter' or 'Bowler'")
    competition_evidence: str = Field(..., description="Format evidence: 'Dual-Format', 'IPL-Only', or 'T20I-Only'")
    cpri_score: float = Field(..., description="Composite Pressure Resilience Index score [0-100]")
    components: CPRIComponents = Field(..., description="The four constituent CPRI components")
    pressure_stats: Dict[str, Any] = Field(..., description="Deliveries, matches, strike rate/economy, residuals under pressure")
    rank_uncertainty: RankUncertainty = Field(..., description="90% bootstrap rank confidence interval and statistics")
    confidence_tier: str = Field(..., description="'High Confidence' vs 'Exploratory' based on sample size and CI width")
    tactical_classification: str = Field(..., description="Grounded tactical classification")
    is_official_top10: bool = Field(..., description="True if within the headline Top 10")
    contextual_splits: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Situational and phase splits")

    # High-Volume CPRI Upgrade Extensions
    adjusted_cpri: Optional[float] = Field(None, description="Volume-adjusted CPRI score [0-100]")
    adjusted_rank: Optional[int] = Field(None, description="Rank ordered by adjusted CPRI")
    ppr_score: Optional[float] = Field(None, description="Pressure Performance Reliability score [0-100]")
    evidence_tier: Optional[str] = Field(None, description="Sample size evidence tier: Elite, Strong, Moderate, Limited, Insufficient")
    is_main_eligible: Optional[bool] = Field(None, description="True if player meets >= 400 pressure balls eligibility for Main Leaderboard")
    eligibility_status: Optional[str] = Field(None, description="'Main Leaderboard', 'Contender / Emerging', or 'Insufficient Evidence'")
    success_rate_pct: Optional[float] = Field(None, description="Percentage of pressure balls with successful clutch execution")
    role_success_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Granular role metrics (dots, boundaries, outs/wickets)")
    adjusted_rank_ci: Optional[str] = Field(None, description="90% bootstrap confidence interval for adjusted rank, e.g. '[1, 5]'")
    last_played: Optional[str] = Field(None, description="Most recent match date in dataset [YYYY-MM-DD]")


class OfficialRoleRankingsResponse(BaseModel):
    role: str = Field(..., description="'Batter' or 'Bowler'")
    title: str = Field(..., description="Display title for official ranking")
    total_official: int = Field(10, description="Total official top 10 players")
    total_candidates: int = Field(..., description="Total candidates in ranking pool")
    official_top10: List[OfficialPlayerItem] = Field(..., description="Ordered list of official Top 10 players")
    pre_floor_baseline: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Pre-floor Baseline (Phase 8) — supplementary unfloored Top 10")
    candidates: List[OfficialPlayerItem] = Field(default_factory=list, description="Contender candidates ranked 11+")
    main_leaderboard: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="High-volume clutch leaderboard (>= 400 balls)")
    contenders: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Contender / Emerging pool (150-399 balls)")
    insufficient_evidence: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Excluded insufficient evidence pool (< 150 balls)")
    evidence_tier_counts: Optional[Dict[str, int]] = Field(default_factory=dict, description="Player counts by evidence tier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Methodology, freeze version, and provenance")


class UnifiedOfficialOverviewResponse(BaseModel):
    version: str = Field(..., description="Methodology freeze version (e.g. CPRI-v1.0.0-PHASE8-OFFICIAL)")
    title: str = Field("SupeRR Intelligence — Official Competition Rankings", description="Headline overview title")
    batters: List[OfficialPlayerItem] = Field(..., description="Official Top 10 Batters")
    bowlers: List[OfficialPlayerItem] = Field(..., description="Official Top 10 Bowlers")
    pre_floor_batters: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Pre-floor Baseline Batters (Phase 8) — supplementary")
    pre_floor_bowlers: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Pre-floor Baseline Bowlers (Phase 8) — supplementary")
    main_leaderboard_batters: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Main Leaderboard Batters (>= 400 balls)")
    main_leaderboard_bowlers: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Main Leaderboard Bowlers (>= 400 balls)")
    contender_batters: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Contender Batters (150-399 balls)")
    contender_bowlers: Optional[List[OfficialPlayerItem]] = Field(default_factory=list, description="Contender Bowlers (150-399 balls)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata, provenance, and timestamp")
