"""
backend/app/api/routes/active.py
API endpoints for currently active professional T20 player rankings and analysis.
Filters confirmed retirees while preserving historical performance data.
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/active", tags=["Active Player Rankings"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
ELIG_DIR = REPO_ROOT / "output" / "eligibility"


@router.get("/rankings")
def get_active_rankings(
    role: Optional[str] = Query("All", description="Player role filter: 'Batter', 'Bowler', 'All-Rounder', or 'All'"),
    min_balls: Optional[int] = Query(0, description="Minimum pressure deliveries filter"),
    evidence_tier: Optional[str] = Query(None, description="Evidence tier: Elite, Strong, Moderate, Limited"),
    limit: Optional[int] = Query(50, description="Number of players to return")
) -> Dict[str, Any]:
    """
    Returns verified active professional T20 players ranked by clutch performance (CPRI).
    Confirmed retirees (e.g. Dinesh Karthik) are excluded.
    """
    summary_path = ELIG_DIR / "active_rankings_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=503, detail="Active rankings summary not generated yet.")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    # Load full rankings if limit > 10
    bat_csv = ELIG_DIR / "active_batters_rankings.csv"
    bowl_csv = ELIG_DIR / "active_bowlers_rankings.csv"
    ar_csv = ELIG_DIR / "active_allrounders_rankings.csv"

    batters = pd.read_csv(bat_csv) if bat_csv.exists() else pd.DataFrame(summary_data["top10_active_batters"])
    bowlers = pd.read_csv(bowl_csv) if bowl_csv.exists() else pd.DataFrame(summary_data["top10_active_bowlers"])
    allrounders = pd.read_csv(ar_csv) if ar_csv.exists() else pd.DataFrame(summary_data["top10_active_allrounders"])

    def _filter_df(df: pd.DataFrame, balls_col: str) -> pd.DataFrame:
        res = df.copy()
        if min_balls and min_balls > 0:
            res = res[res[balls_col] >= min_balls]
        if evidence_tier:
            res = res[res["evidence_tier"].str.contains(evidence_tier, case=False, na=False)]
        return res.head(limit)

    result: Dict[str, Any] = {
        "metadata": summary_data["metadata"],
        "filters_applied": {
            "role": role,
            "min_balls": min_balls,
            "evidence_tier": evidence_tier,
            "limit": limit
        }
    }

    role_clean = role.lower() if role else "all"

    if role_clean in ("all", "batter", "batters"):
        f_bat = _filter_df(batters, "pressure_deliveries")
        result["active_batters"] = f_bat.to_dict(orient="records")

    if role_clean in ("all", "bowler", "bowlers"):
        f_bowl = _filter_df(bowlers, "pressure_deliveries")
        result["active_bowlers"] = f_bowl.to_dict(orient="records")

    if role_clean in ("all", "all-rounder", "allrounder", "all-rounders"):
        f_ar = _filter_df(allrounders, "total_pressure_balls")
        result["active_allrounders"] = f_ar.to_dict(orient="records")

    return result
