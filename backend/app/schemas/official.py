"""
backend/app/schemas/official.py
Pydantic schemas for the authoritative official Phase 8 CPRI rankings.
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


class OfficialRoleRankingsResponse(BaseModel):
    role: str = Field(..., description="'Batter' or 'Bowler'")
    title: str = Field(..., description="Display title for official ranking")
    total_official: int = Field(10, description="Total official top 10 players")
    total_candidates: int = Field(..., description="Total candidates in ranking pool")
    official_top10: List[OfficialPlayerItem] = Field(..., description="Ordered list of official Top 10 players")
    candidates: List[OfficialPlayerItem] = Field(default_factory=list, description="Contender candidates ranked 11+")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Methodology, freeze version, and provenance")


class UnifiedOfficialOverviewResponse(BaseModel):
    version: str = Field(..., description="Methodology freeze version (e.g. CPRI-v1.0.0-PHASE8-OFFICIAL)")
    title: str = Field("SupeRR Intelligence — Official Competition Rankings", description="Headline overview title")
    batters: List[OfficialPlayerItem] = Field(..., description="Official Top 10 Batters")
    bowlers: List[OfficialPlayerItem] = Field(..., description="Official Top 10 Bowlers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata, provenance, and timestamp")
