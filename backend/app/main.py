"""
backend/app/main.py
Main FastAPI application entry point for SupeRR Intelligence API.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    SupeRRException,
    superr_exception_handler,
    validation_exception_handler
)
from backend.app.services.scouting_service import ScoutingService
from backend.app.api.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Initializes the in-memory ScoutingService on startup to pre-load all stores.
    """
    print(f"Initializing SupeRR Intelligence Backend (v{settings.VERSION})...")
    service = ScoutingService()
    app.state.scouting_service = service
    health = service.get_health_status()
    print(f"Data Stores Loaded: {health['stores_loaded']} from {health['data_dir']}")
    print(f"Active Inference Tier: {health['tier_available']}")
    yield
    print("Shutting down SupeRR Intelligence Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
app.add_exception_handler(SupeRRException, superr_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_status():
    """Root welcoming endpoint with links to documentation."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "health": f"{settings.API_V1_STR}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
