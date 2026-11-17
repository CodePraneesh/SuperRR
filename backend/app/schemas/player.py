"""
backend/app/schemas/player.py
Pydantic schemas for player profiles, cohort rankings, and contextual splits.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CPRIComponents(BaseModel):
    pressure_impact: float = Field(..., description="Pressure Impact component score (40% weight)")
    pressure_adaptability: float = Field(..., description="Pressure Adaptability component score (25% weight)")
    clutch_consistency: float = Field(..., description="Clutch Consistency component score (20% weight)")
    reliability_confidence: float = Field(..., description="Reliability Confidence component score (15% weight)")


class PlayerSummaryItem(BaseModel):
    player_id: Optional[int] = Field(None, description="Numeric player ID")
    player_name: str = Field(..., description="Official player name")
    competition_scope: str = Field(..., description="Competition scope (IPL or T20I)")
    role: str = Field(..., description="Player role (Batter or Bowler)")
    cohort: str = Field(..., description="Full cohort name, e.g. 'IPL Batters'")
    official_rank: Optional[int] = Field(None, description="Official frozen rank (1-10) or None if unranked")
    ranking_tier: str = Field(..., description="Ranking tier (Official Top 10, Provisional, Unranked)")
    confidence_tier: str = Field(..., description="Sample confidence tier (High Confidence, Medium Confidence, etc.)")
    is_official_top10: bool = Field(..., description="Whether player is in official frozen Top 10")
    is_official_ranked: bool = Field(..., description="Whether player is in official frozen Top 10")
    cpri_score: float = Field(..., description="Composite Pressure Resilience Index score [0-100]")
    components: CPRIComponents = Field(..., description="Four CPRI component scores")
    pressure_deliveries: int = Field(..., description="Authoritative frozen pressure deliveries faced/bowled")
    strike_rate: Optional[float] = Field(None, description="Overall strike rate for batters")
    economy_rate: Optional[float] = Field(None, description="Overall economy rate for bowlers")


class CohortListResponse(BaseModel):
    competition_scope: str = Field(..., description="Requested competition scope")
    role: str = Field(..., description="Requested role")
    cohort: str = Field(..., description="Cohort identifier")
    view_type: str = Field("contextual_league_view", description="Indicates this is a single-tournament slice, not the official competition ranking")
    disclaimer: str = Field(
        "Contextual league view, not the official ranking. The authoritative competition ranking is the Official Phase 13 ranking (≥250 pressure balls) at /api/v1/official.",
        description="Official ranking notice"
    )
    total_players: int = Field(..., description="Total players matching criteria in cohort")
    official_count: int = Field(..., description="Number of official Top 10 players in cohort")
    limit: int = Field(..., description="Pagination limit")
    offset: int = Field(..., description="Pagination offset")
    players: List[PlayerSummaryItem] = Field(..., description="List of player summary records")


class PlayerProfileResponse(BaseModel):
    player_id: Optional[int] = Field(None, description="Numeric player ID")
    player_name: str = Field(..., description="Official player name")
    competition_scope: str = Field(..., description="Competition scope (IPL or T20I)")
    role: str = Field(..., description="Player role (Batter or Bowler)")
    cohort: str = Field(..., description="Cohort identifier")
    official_rank: Optional[int] = Field(None, description="Official rank (1-10) or None")
    ranking_tier: str = Field(..., description="Ranking tier description")
    confidence_tier: str = Field(..., description="Confidence tier")
    is_official_top10: bool = Field(..., description="True if official Top 10")
    is_official_ranked: Optional[bool] = Field(None, description="True if official Top 10")
    cpri_score: float = Field(..., description="Composite CPRI score")
    components: CPRIComponents = Field(..., description="Four CPRI component scores")
    exposure: Dict[str, Any] = Field(..., description="Sample exposure metrics")
    performance_stats: Dict[str, Any] = Field(..., description="Detailed batting or bowling performance statistics")
    peer_benchmarks: Optional[Dict[str, Any]] = Field(None, description="Percentiles and benchmarking vs cohort peers")
    strengths_and_weaknesses: Optional[Dict[str, Any]] = Field(None, description="Empirical strengths and vulnerabilities")


class ContextualSplitsResponse(BaseModel):
    player_name: str = Field(..., description="Player name")
    competition_scope: str = Field(..., description="Competition scope")
    role: str = Field(..., description="Player role")
    innings_phase_splits: Dict[str, Any] = Field(..., description="Powerplay, Middle, Death overs splits")
    pressure_contrast: Dict[str, Any] = Field(..., description="High pressure (PI>=50) vs Low pressure (PI<50) contrast")
    bowling_type_splits: Optional[Dict[str, Any]] = Field(None, description="Pace vs Spin splits (Batters only)")
    batter_hand_splits: Optional[Dict[str, Any]] = Field(None, description="RHB vs LHB splits (Bowlers only)")
