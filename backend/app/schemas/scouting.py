"""
backend/app/schemas/scouting.py
Pydantic schemas for AI scouting reports, comparisons, matchups, and natural-language QA.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScoutingReportResponse(BaseModel):
    status: str = Field(..., description="Generation execution status", example="success")
    player_name: str = Field(..., description="Player name")
    competition_scope: str = Field(..., description="Competition scope (IPL or T20I)")
    role: str = Field(..., description="Player role (Batter or Bowler)")
    feature: str = Field(..., description="Feature identifier", example="player_scouting_report")
    tier_used: str = Field(..., description="Inference tier used for generation", example="Tier 3: Deterministic Fallback Engine")
    model_name: str = Field(..., description="Name of generating model or rule engine")
    verified: bool = Field(..., description="Whether response passed strict numerical verification")
    verification_notes: List[str] = Field(default_factory=list, description="Verification notes or discrepancy audits")
    response: str = Field(..., description="Complete scouting report in GitHub Flavored Markdown")
    sample_limitations: List[str] = Field(default_factory=list, description="Documented sample constraints")


class PressureExplanationResponse(BaseModel):
    status: str = Field(..., description="Execution status")
    player_name: str = Field(..., description="Player name")
    competition_scope: str = Field(..., description="Competition scope")
    role: str = Field(..., description="Player role")
    feature: str = Field(..., description="Feature identifier", example="explain_pressure_performance")
    tier_used: str = Field(..., description="Inference tier used")
    model_name: str = Field(..., description="Model or engine used")
    verified: bool = Field(..., description="Whether response passed verification")
    verification_notes: List[str] = Field(default_factory=list)
    response: str = Field(..., description="Pressure performance narrative breakdown")
    sample_limitations: List[str] = Field(default_factory=list)


class PlayerComparisonRequest(BaseModel):
    scope: str = Field("IPL", description="Competition scope ('IPL' or 'T20I')")
    role: str = Field("Batter", description="Role to compare ('Batter' or 'Bowler')")
    player_a: str = Field(..., description="Name of first player", example="Rinku Singh")
    player_b: str = Field(..., description="Name of second player", example="Andre Russell")


class PlayerComparisonResponse(BaseModel):
    status: str = Field(..., description="Execution status")
    comparison_scope: str = Field(..., description="Competition scope")
    role: str = Field(..., description="Comparison role")
    player_a: str = Field(..., description="Name of player A")
    player_b: str = Field(..., description="Name of player B")
    structured_comparison: Dict[str, Any] = Field(..., description="Deterministic side-by-side metrics and component deltas")
    ai_analysis: str = Field(..., description="Analytical comparative report")
    tier_used: str = Field(..., description="Inference tier used")
    model_name: str = Field(..., description="Model name")
    verified: bool = Field(..., description="Verification status")
    verification_notes: List[str] = Field(default_factory=list)
    sample_limitations: List[str] = Field(default_factory=list)


class MatchupResponse(BaseModel):
    status: str = Field(..., description="Execution status")
    competition_scope: str = Field(..., description="Competition scope")
    batter_name: str = Field(..., description="Batter name")
    bowler_name: str = Field(..., description="Bowler name")
    h2h_data: Dict[str, Any] = Field(..., description="Statistical encounter summary")
    ai_narrative: str = Field(..., description="Matchup narrative analysis")
    tier_used: str = Field(..., description="Inference tier used")
    model_name: str = Field(..., description="Model name")
    verified: bool = Field(..., description="Verification status")
    is_small_sample: bool = Field(..., description="True if sample is under statistical threshold (<18 balls)")
    sample_tier: str = Field(..., description="Sample tier description")
    sample_warning: Optional[str] = Field(None, description="Prominent sample warning if exploratory (<18 balls)")


class AnalyticsQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question", example="Who is the best death-overs finisher under pressure?")
    scope: Optional[str] = Field(None, description="Optional scope filter ('IPL' or 'T20I')")
    role: Optional[str] = Field(None, description="Optional role filter ('Batter' or 'Bowler')")
    target_entities: Optional[List[str]] = Field(None, description="Optional list of specific player names")


class AnalyticsQueryResponse(BaseModel):
    status: str = Field(..., description="Execution status")
    query: str = Field(..., description="Original user query")
    scope: Optional[str] = Field(None, description="Scope filter applied")
    answer: str = Field(..., description="Grounded analytical response")
    tier_used: str = Field(..., description="Inference tier used")
    model_name: str = Field(..., description="Model name")
    verified: bool = Field(..., description="Verification status")
    verification_notes: List[str] = Field(default_factory=list)
    evidence_summary: Optional[Dict[str, Any]] = Field(None, description="Verified entity profiles used in response")
