"""
backend/app/api/routes/official.py
Authoritative official Phase 8 competition rankings, bootstrap uncertainty,
and High-Volume Pressure Performance Reliability (PPR) endpoints.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from backend.app.schemas.official import (
    OfficialRoleRankingsResponse,
    UnifiedOfficialOverviewResponse,
    OfficialPlayerItem
)
from backend.app.dependencies import get_scouting_service
from backend.app.services.scouting_service import ScoutingService

router = APIRouter(prefix="/official", tags=["Official Rankings"])


def filter_players_list(
    players: List[Dict[str, Any]],
    min_balls: Optional[int] = None,
    evidence_tier: Optional[str] = None,
    format_evidence: Optional[str] = None
) -> list:
    """Filter player items/dicts by min_balls, evidence_tier, and format_evidence."""
    out = []
    for p in players:
        # p can be OfficialPlayerItem or dict
        p_balls = p.pressure_stats.get("pressure_deliveries", 0) if hasattr(p, "pressure_stats") else p.get("pressure_stats", {}).get("pressure_deliveries", 0)
        p_tier = getattr(p, "evidence_tier", None) if hasattr(p, "evidence_tier") else p.get("evidence_tier")
        p_format = getattr(p, "competition_evidence", None) if hasattr(p, "competition_evidence") else p.get("competition_evidence")

        if min_balls is not None and p_balls < min_balls:
            continue
        if evidence_tier and p_tier and p_tier.lower() != evidence_tier.lower():
            continue
        if format_evidence and p_format and p_format.lower() != format_evidence.lower():
            continue
        out.append(p)
    return out


@router.get(
    "/rankings",
    response_model=UnifiedOfficialOverviewResponse,
    summary="Get authoritative official Top 10 rankings and High-Volume leaderboards"
)
def get_official_unified_rankings(
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns the headline official competition Top 10 batters and bowlers
    frozen in Phase 8, alongside High-Volume Main Leaderboards (>= 400 pressure balls)
    and Contender pools with bootstrap rank confidence intervals.
    """
    return service.get_official_rankings()


@router.get(
    "/batters",
    response_model=OfficialRoleRankingsResponse,
    summary="Get official Top 10 batters, candidates, and high-volume main leaderboard"
)
def get_official_batters(
    min_balls: Optional[int] = Query(None, description="Minimum pressure deliveries filter (e.g. 400, 250, 150)"),
    evidence_tier: Optional[str] = Query(None, description="Filter by Evidence Tier (e.g. 'Elite Evidence')"),
    format_evidence: Optional[str] = Query(None, description="Filter by format: 'Dual-Format', 'IPL-Only', 'T20I-Only'"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns official Top 10 batters (led by Matthew Wade at CPRI 85.36)
    and High-Volume Main Leaderboard (led by Suryakumar Yadav and Tim David).
    """
    res = service.get_official_rankings(role="Batter")
    if min_balls or evidence_tier or format_evidence:
        res["main_leaderboard"] = filter_players_list(res.get("main_leaderboard", []), min_balls, evidence_tier, format_evidence)
        res["contenders"] = filter_players_list(res.get("contenders", []), min_balls, evidence_tier, format_evidence)
        res["official_top10"] = filter_players_list(res.get("official_top10", []), min_balls, evidence_tier, format_evidence)
    return res


@router.get(
    "/bowlers",
    response_model=OfficialRoleRankingsResponse,
    summary="Get official Top 10 bowlers, candidates, and high-volume main leaderboard"
)
def get_official_bowlers(
    min_balls: Optional[int] = Query(None, description="Minimum pressure deliveries filter (e.g. 400, 250, 150)"),
    evidence_tier: Optional[str] = Query(None, description="Filter by Evidence Tier (e.g. 'Elite Evidence')"),
    format_evidence: Optional[str] = Query(None, description="Filter by format: 'Dual-Format', 'IPL-Only', 'T20I-Only'"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns official Top 10 bowlers (led by Mitchell Santner at CPRI 79.84)
    and High-Volume Main Leaderboard (led by Rashid Khan and Mitchell Santner).
    """
    res = service.get_official_rankings(role="Bowler")
    if min_balls or evidence_tier or format_evidence:
        res["main_leaderboard"] = filter_players_list(res.get("main_leaderboard", []), min_balls, evidence_tier, format_evidence)
        res["contenders"] = filter_players_list(res.get("contenders", []), min_balls, evidence_tier, format_evidence)
        res["official_top10"] = filter_players_list(res.get("official_top10", []), min_balls, evidence_tier, format_evidence)
    return res


@router.get(
    "/player/{name}",
    response_model=OfficialPlayerItem,
    summary="Get official unified player ranking, CPRI score, PPR score, and rank uncertainty"
)
def get_official_player(
    name: str = Path(..., description="Player name (e.g. 'Matthew Wade' or 'Suryakumar Yadav')"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Retrieves the official unified record for a player, including their
    official rank, CPRI score, Adjusted CPRI, PPR score, evidence tier, and 90% rank CI.
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
    min_balls: Optional[int] = Query(None, description="Minimum pressure deliveries filter"),
    evidence_tier: Optional[str] = Query(None, description="Filter by Evidence Tier"),
    format_evidence: Optional[str] = Query(None, description="Filter by format"),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Returns official Top 10 rankings, candidates, and high-volume main leaderboard for the requested role.
    """
    role_norm = role.rstrip("s").capitalize()
    if role_norm not in ("Batter", "Bowler"):
        raise HTTPException(status_code=422, detail=f"Invalid role '{role}'. Must be 'Batter' or 'Bowler'.")
    res = service.get_official_rankings(role=role_norm)
    if min_balls or evidence_tier or format_evidence:
        res["main_leaderboard"] = filter_players_list(res.get("main_leaderboard", []), min_balls, evidence_tier, format_evidence)
        res["contenders"] = filter_players_list(res.get("contenders", []), min_balls, evidence_tier, format_evidence)
        res["official_top10"] = filter_players_list(res.get("official_top10", []), min_balls, evidence_tier, format_evidence)
    return res
