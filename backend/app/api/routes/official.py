"""
backend/app/api/routes/official.py
Authoritative official Phase 8 competition rankings and uncertainty endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Path, HTTPException
from backend.app.schemas.official import (
    OfficialRoleRankingsResponse,
    UnifiedOfficialOverviewResponse,
    OfficialPlayerItem
)
from backend.app.dependencies import get_scouting_service
from backend.app.services.scouting_service import ScoutingService

router = APIRouter(prefix="/official", tags=["Official Rankings"])


@router.get(
    "/rankings",
    response_model=UnifiedOfficialOverviewResponse,
    summary="Get authoritative official Top 10 rankings for both batters and bowlers"
)
def get_official_unified_rankings(
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns the headline official competition Top 10 batters and bowlers
    frozen in Phase 8, complete with 90% bootstrap rank confidence intervals.
    """
    return service.get_official_rankings()


@router.get(
    "/batters",
    response_model=OfficialRoleRankingsResponse,
    summary="Get official Top 10 batters and candidates with 90% rank CIs"
)
def get_official_batters(
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns official Top 10 batters (led by Matthew Wade at CPRI 85.36)
    and contender candidates with bootstrap rank uncertainty.
    """
    return service.get_official_rankings(role="Batter")


@router.get(
    "/bowlers",
    response_model=OfficialRoleRankingsResponse,
    summary="Get official Top 10 bowlers and candidates with 90% rank CIs"
)
def get_official_bowlers(
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns official Top 10 bowlers (led by Mitchell Santner at CPRI 79.84)
    and contender candidates with bootstrap rank uncertainty.
    """
    return service.get_official_rankings(role="Bowler")


@router.get(
    "/player/{name}",
    response_model=OfficialPlayerItem,
    summary="Get official unified player ranking, CPRI score, and rank uncertainty"
)
def get_official_player(
    name: str = Path(..., description="Player name (e.g. 'Matthew Wade' or 'Rinku Singh')"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Retrieves the official unified record for a player, including their
    official rank, CPRI score, component breakdown, and 90% rank confidence interval.
    """
    try:
        return service.get_official_player(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found in official ranking stores.")


@router.get(
    "/{role}",
    response_model=OfficialRoleRankingsResponse,
    summary="Get official rankings for a specified role ('Batter' or 'Bowler')"
)
def get_official_by_role(
    role: str = Path(..., description="Role: 'Batter' or 'Bowler' (or 'batters'/'bowlers')"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns the official Top 10 rankings and candidates for the requested role.
    """
    role_norm = role.rstrip("s").capitalize()
    if role_norm not in ("Batter", "Bowler"):
        raise HTTPException(status_code=422, detail=f"Invalid role '{role}'. Must be 'Batter' or 'Bowler'.")
    return service.get_official_rankings(role=role_norm)
