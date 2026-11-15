"""
backend/app/dependencies.py
FastAPI dependency injection providers.
"""
from typing import Optional
from fastapi import Request
from backend.app.services.scouting_service import ScoutingService

_singleton_service: Optional[ScoutingService] = None


def get_scouting_service(request: Request) -> ScoutingService:
    """
    Dependency returning the active ScoutingService instance.
    Prefers the lifespan app.state instance, falling back to a cached module singleton.
    """
    if hasattr(request.app.state, "scouting_service") and request.app.state.scouting_service is not None:
        return request.app.state.scouting_service

    global _singleton_service
    if _singleton_service is None:
        _singleton_service = ScoutingService()
    return _singleton_service
