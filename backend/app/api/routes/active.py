"""
backend/app/api/routes/active.py
API endpoints for supplementary 'recently active in data' (last 12 months) rankings.
Governed strictly by docs/methodology/v5/ELIGIBILITY_RULE.md.
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import pandas as pd
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/active", tags=["Supplementary Active Rankings"])

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
ACTIVE_DIR = REPO_ROOT / "output" / "phase12_active"


@router.get("/rankings")
def get_active_rankings(
    role: Optional[str] = Query("All", description="Player role filter: 'Batter', 'Bowler', or 'All'"),
    min_balls: Optional[int] = Query(0, description="Minimum pressure deliveries filter"),
    evidence_tier: Optional[str] = Query(None, description="Evidence tier: Elite, Strong, Moderate, Limited"),
    limit: Optional[int] = Query(50, description="Number of players to return")
) -> Dict[str, Any]:
    """
    Returns players recently active in the match dataset (last 12 months),
    ranked strictly by RAW CPRI under the post-hoc eligibility window.
    """
    summary_path = ACTIVE_DIR / "active_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=503, detail="Active rankings summary not generated yet.")

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    # Load top 25 rankings if limit > 10, else top 10
    bat_csv = ACTIVE_DIR / ("active_top25_batters.csv" if limit > 10 else "active_top10_batters.csv")
    bowl_csv = ACTIVE_DIR / ("active_top25_bowlers.csv" if limit > 10 else "active_top10_bowlers.csv")

    batters = pd.read_csv(bat_csv) if bat_csv.exists() else pd.DataFrame(summary_data["active_top10_batters"])
    bowlers = pd.read_csv(bowl_csv) if bowl_csv.exists() else pd.DataFrame(summary_data["active_top10_bowlers"])

    def _filter_df(df: pd.DataFrame) -> pd.DataFrame:
        res = df.copy()
        if min_balls and min_balls > 0:
            res = res[res["pressure_deliveries"] >= min_balls]
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
        f_bat = _filter_df(batters)
        result["active_batters"] = f_bat.to_dict(orient="records")

    if role_clean in ("all", "bowler", "bowlers"):
        f_bowl = _filter_df(bowlers)
        result["active_bowlers"] = f_bowl.to_dict(orient="records")

    return result


@router.get("/sensitivity")
def get_active_sensitivity() -> Dict[str, Any]:
    """
    Returns the sensitivity table across 6, 12, and 18-month activity windows.
    """
    sens_csv = ACTIVE_DIR / "active_sensitivity_table.csv"
    if not sens_csv.exists():
        raise HTTPException(status_code=503, detail="Sensitivity analysis table not generated yet.")

    df = pd.read_csv(sens_csv)
    return {
        "windows": df.to_dict(orient="records")
    }
