"""
backend/app/schemas/common.py
Common Pydantic schemas for health, system status, and standard error envelopes.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="System health status", json_schema_extra={"example": "healthy"})
    version: str = Field(..., description="API version", json_schema_extra={"example": "1.0.0"})
    stores_loaded: bool = Field(..., description="Whether Phase 4 scouting stores are loaded in memory", json_schema_extra={"example": True})
    offline_mode: bool = Field(..., description="Whether operating in offline deterministic mode", json_schema_extra={"example": False})
    tier_available: str = Field(..., description="Highest AI inference tier available", json_schema_extra={"example": "Tier 1: Hugging Face API"})
    data_dir: str = Field(..., description="Path to active data store directory")
    timestamp: str = Field(..., description="Current ISO-8601 server timestamp")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error description")
    error_type: str = Field(..., description="Machine-readable error type code")
    status_code: int = Field(..., description="HTTP status code")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed validation errors if applicable")
