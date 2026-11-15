"""
backend/app/core/config.py
Configuration settings for SupeRR Intelligence FastAPI backend.
"""
import os
import sys
from pathlib import Path
from typing import List

# Ensure base directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


class Settings:
    PROJECT_NAME: str = "SupeRR Intelligence API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Production AI cricket scouting backend delivering frozen CPRI v1.0.0 rankings, "
        "evidence-grounded AI scouting reports, situational splits, and matchup analysis."
    )
    API_V1_STR: str = "/api/v1"
    
    # Server configuration
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Data directory containing frozen Phase 4 scouting stores
    DATA_DIR: Path = BASE_DIR / "output" / "phase4" / "data"

    # AI Model Configuration
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    PRIMARY_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"

    # CORS Origins for React frontends
    _cors_env = os.getenv("CORS_ORIGINS")
    CORS_ORIGINS: List[str] = (
        [orig.strip() for orig in _cors_env.split(",") if orig.strip()]
        if _cors_env
        else [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "*",
        ]
    )


settings = Settings()
