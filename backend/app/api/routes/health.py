"""
backend/app/api/routes/health.py
System health and readiness endpoint.
"""
from fastapi import APIRouter, Depends
from backend.app.schemas.common import HealthResponse
from backend.app.dependencies import get_scouting_service
from backend.app.services.scouting_service import ScoutingService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Check API health and loaded stores")
def check_health(service: ScoutingService = Depends(get_scouting_service)):
    """
    Returns system status, active version, store readiness, and inference capability.
    """
    return service.get_health_status()
