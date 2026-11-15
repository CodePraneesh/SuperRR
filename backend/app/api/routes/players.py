"""
backend/app/api/routes/players.py
Player cohort listings, profile retrieval, and contextual split endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from backend.app.schemas.player import (
    CohortListResponse,
    PlayerProfileResponse,
    ContextualSplitsResponse
)
from backend.app.dependencies import get_scouting_service
from backend.app.services.scouting_service import ScoutingService

router = APIRouter(prefix="/players", tags=["Players"])


@router.get(
    "/{scope}/{role}",
    response_model=CohortListResponse,
    summary="List cohort players with CPRI scores and rankings"
)
def list_cohort_players(
    scope: str = Path(..., description="Competition scope: 'IPL' or 'T20I'", examples=["IPL"]),
    role: str = Path(..., description="Player role: 'Batter' or 'Bowler'", examples=["Batter"]),
    official_only: bool = Query(False, description="Filter only frozen official Top 10 ranked players"),
    confidence_tier: Optional[str] = Query(None, description="Filter by confidence tier, e.g. 'High Confidence'"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns sorted list of players within an official competition scope and role cohort.
    Strictly isolates IPL from T20I and Batters from Bowlers.
    """
    return service.get_cohort_players(
        scope=scope,
        role=role,
        official_only=official_only,
        confidence_tier=confidence_tier,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{scope}/{role}/{name}",
    response_model=PlayerProfileResponse,
    summary="Get full player profile, CPRI components, and benchmarks"
)
def get_player_profile(
    scope: str = Path(..., description="Competition scope: 'IPL' or 'T20I'", examples=["IPL"]),
    role: str = Path(..., description="Player role: 'Batter' or 'Bowler'", examples=["Batter"]),
    name: str = Path(..., description="Player name", examples=["Rinku Singh"]),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Retrieves a comprehensive player profile with official CPRI v1.0.0 score,
    the four constituent components, empirical percentiles vs cohort peers,
    and verified strengths and weaknesses.
    """
    return service.get_player_profile(name=name, scope=scope, role=role)


@router.get(
    "/{scope}/{role}/{name}/splits",
    response_model=ContextualSplitsResponse,
    summary="Get situational phase and pressure contrast splits"
)
def get_player_splits(
    scope: str = Path(..., description="Competition scope: 'IPL' or 'T20I'", examples=["IPL"]),
    role: str = Path(..., description="Player role: 'Batter' or 'Bowler'", examples=["Batter"]),
    name: str = Path(..., description="Player name", examples=["Rinku Singh"]),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns situational performance metrics:
    - Phase splits: Powerplay (overs 1-6), Middle (7-16), Death (17-20)
    - Pressure contrast: High pressure (PI >= 50) vs Low pressure (PI < 50)
    - Pace vs Spin (Batters) or RHB vs LHB (Bowlers)
    """
    return service.get_player_splits(name=name, scope=scope, role=role)
