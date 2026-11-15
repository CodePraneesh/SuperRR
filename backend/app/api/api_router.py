"""
backend/app/api/api_router.py
Unified router mounting health, players, and scouting routes.
"""
from fastapi import APIRouter
from backend.app.api.routes import health, players, scouting, official

api_router = APIRouter()

api_router.include_router(official.router)
api_router.include_router(health.router)
api_router.include_router(players.router)
api_router.include_router(scouting.router)
