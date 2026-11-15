"""
backend/app/api/routes/scouting.py
AI scouting reports, pressure explanations, comparisons, matchups, and natural-language QA.
"""
from fastapi import APIRouter, Depends, Path
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


@router.post(
    "/ask",
    response_model=AnalyticsQueryResponse,
    summary="Answer natural language cricket scouting and analytics query"
)
def ask_question(
    payload: AnalyticsQueryRequest,
    service: ScoutingService = Depends(get_scouting_service)
):
    """
    Answers natural-language cricket queries grounded strictly in verified statistical evidence.
    Never hallucinates unrecorded metrics or attributes.
    """
    return service.ask_analytics_question(
        query=payload.query,
        scope=payload.scope,
        role=payload.role,
        target_entities=payload.target_entities
    )
