"""
backend/app/api/routes/scouting.py
AI scouting reports, pressure explanations, comparisons, matchups, and natural-language QA.
"""
import time
from collections import defaultdict
from fastapi import APIRouter, Depends, Path, Request, HTTPException
from backend.app.schemas.scouting import (
    ScoutingReportResponse,
    PressureExplanationResponse,
    PlayerComparisonRequest,
    PlayerComparisonResponse,
    MatchupResponse,
    AnalyticsQueryRequest,
    AnalyticsQueryResponse
)
from backend.app.dependencies import get_scouting_service
from backend.app.services.scouting_service import ScoutingService

router = APIRouter(prefix="/scouting", tags=["Scouting"])


@router.get(
    "/report/{scope}/{role}/{name}",
    response_model=ScoutingReportResponse,
    summary="Generate evidence-grounded AI scouting report"
)
def get_scouting_report(
    scope: str = Path(..., description="Competition scope ('IPL' or 'T20I')", examples=["IPL"]),
    role: str = Path(..., description="Player role ('Batter' or 'Bowler')", examples=["Batter"]),
    name: str = Path(..., description="Player name", examples=["Rinku Singh"]),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Generates a full AI player scouting report grounded strictly in verified CPRI components,
    cohort peer benchmarks, situational splits, and empirical strengths and weaknesses.
    """
    return service.get_scouting_report(name=name, scope=scope, role=role)


@router.get(
    "/pressure/{scope}/{role}/{name}",
    response_model=PressureExplanationResponse,
    summary="Generate AI explanation of player's pressure performance"
)
def explain_pressure_performance(
    scope: str = Path(..., description="Competition scope ('IPL' or 'T20I')", examples=["IPL"]),
    role: str = Path(..., description="Player role ('Batter' or 'Bowler')", examples=["Batter"]),
    name: str = Path(..., description="Player name", examples=["Rinku Singh"]),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Explains the player's performance under match-state pressure (Pressure Index >= 50)
    contrasted against low-pressure situations, with net strike rate/economy deltas.
    """
    return service.get_pressure_explanation(name=name, scope=scope, role=role)


@router.post(
    "/compare",
    response_model=PlayerComparisonResponse,
    summary="Conduct side-by-side player comparison"
)
def compare_players(
    payload: PlayerComparisonRequest,
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Compares two players within the same format and role, calculating CPRI score deltas,
    component-by-component variance, phase execution comparisons, and tactical narrative.
    """
    return service.compare_players(
        player_a=payload.player_a,
        player_b=payload.player_b,
        scope=payload.scope,
        role=payload.role
    )


@router.get(
    "/matchup/{scope}/{batter}/{bowler}",
    response_model=MatchupResponse,
    summary="Get batter vs bowler head-to-head record and scouting narrative"
)
def get_matchup(
    scope: str = Path(..., description="Competition scope ('IPL' or 'T20I')", examples=["IPL"]),
    batter: str = Path(..., description="Batter name", examples=["Virat Kohli"]),
    bowler: str = Path(..., description="Bowler name", examples=["Jasprit Bumrah"]),
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Retrieves head-to-head encounter metrics between batter and bowler in a specific competition format.
    Includes explicit small-sample warnings if the encounter is below 18 legal deliveries.
    """
    return service.get_matchup(batter=batter, bowler=bowler, scope=scope)


# In-memory sliding-window rate limiter (30 requests/minute per client IP)
_RATE_LIMIT_WINDOW = 60.0
_MAX_REQUESTS_PER_WINDOW = 30
_request_history = defaultdict(list)


def check_rate_limit(client_ip: str) -> None:
    now = time.time()
    history = _request_history[client_ip]
    cutoff = now - _RATE_LIMIT_WINDOW
    _request_history[client_ip] = [t for t in history if t > cutoff]
    if len(_request_history[client_ip]) >= _MAX_REQUESTS_PER_WINDOW:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: maximum 30 queries per minute per client. Please retry shortly."
        )
    _request_history[client_ip].append(now)


@router.post(
    "/ask",
    response_model=AnalyticsQueryResponse,
    summary="Answer natural language cricket scouting and analytics query"
)
def ask_question(
    payload: AnalyticsQueryRequest,
    request: Request,
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Answers natural-language cricket queries grounded strictly in verified statistical evidence.
    Never hallucinates unrecorded metrics or attributes.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    check_rate_limit(client_ip)

    clean_query = payload.query.strip()
    if len(clean_query) < 3:
        raise HTTPException(status_code=422, detail="Query must be at least 3 characters.")
    if len(clean_query) > 500:
        raise HTTPException(status_code=422, detail="Query must not exceed 500 characters.")

    return service.ask_analytics_question(
        query=clean_query,
        scope=payload.scope,
        role=payload.role,
        target_entities=payload.target_entities
    )
