"""
ml/phase11_v2/data_loader.py
Loads, cleans, validates, and partitions delivery and match datasets for v2 pipeline.
"""
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def load_v2_datasets(pressure_threshold: float = 50.0):
    """
    Loads and merges in-scope delivery and match datasets.
    Returns:
        matches_df: in-scope matches sorted chronologically
        batters_df: delivery-level batter dataset
        bowlers_df: delivery-level bowler dataset
    """
    matches_path = REPO_ROOT / "output" / "processed" / "matches_enriched.csv"
    b_path = REPO_ROOT / "output" / "phase2" / "batter_delivery_expectations.csv"
    bw_path = REPO_ROOT / "output" / "phase2" / "bowler_delivery_expectations.csv"
    w_path = REPO_ROOT / "output" / "phase2" / "delivery_wpa.csv"
    
    # 1. Matches
    matches = pd.read_csv(matches_path, low_memory=False)
    matches_in = matches[matches["competition_scope"].isin(["IPL", "T20I"])].copy()
    matches_in["match_date"] = pd.to_datetime(matches_in["match_date"])
    matches_in = matches_in.sort_values("match_date").reset_index(drop=True)
    in_scope_ids = set(matches_in["match_id"])
    
    # 2. Batters
    b_df = pd.read_csv(b_path, low_memory=False)
    b_df = b_df[b_df["match_id"].isin(in_scope_ids)].copy()
    
    # 3. Bowlers
    bw_df = pd.read_csv(bw_path, low_memory=False)
    bw_df = bw_df[bw_df["match_id"].isin(in_scope_ids)].copy()
    
    # 4. Delivery WPA
    w_df = pd.read_csv(w_path, low_memory=False)
    w_df = w_df[w_df["match_id"].isin(in_scope_ids)].copy()
    
    # Merge WPA
    wpa_cols = ["match_id", "innings", "overid", "over_ball_num", "batting_wpa", "bowling_wpa"]
    b_df = b_df.merge(w_df[wpa_cols], on=["match_id", "innings", "overid", "over_ball_num"], how="left")
    b_df["batting_wpa"] = b_df["batting_wpa"].fillna(0.0)
    
    bw_df = bw_df.merge(w_df[wpa_cols], on=["match_id", "innings", "overid", "over_ball_num"], how="left")
    bw_df["bowling_wpa"] = bw_df["bowling_wpa"].fillna(0.0)
    
    # Ensure match_date in deliveries is datetime
    b_df["match_date"] = pd.to_datetime(b_df["match_date"])
    bw_df["match_date"] = pd.to_datetime(bw_df["match_date"])
    
    # Pressure flags
    b_df["is_pressure"] = b_df["pressure_score"] >= pressure_threshold
    bw_df["is_pressure"] = bw_df["pressure_score"] >= pressure_threshold
    
    # Raw per-delivery net value added
    # Batters: run residual + 12 * survival residual + 25 * batting WPA
    b_df["net_value_raw"] = (
        b_df["batting_run_residual"] + 
        12.0 * b_df["batting_dismissal_residual"] + 
        25.0 * b_df["batting_wpa"]
    )
    
    # Bowlers: runs saved + 12 * wicket residual + 25 * bowling WPA
    bw_df["net_value_raw"] = (
        bw_df["bowling_run_residual"] + 
        12.0 * bw_df["bowling_wicket_residual"] + 
        25.0 * bw_df["bowling_wpa"]
    )
    
    return matches_in, b_df, bw_df

def get_eligible_players(
    deliv_df: pd.DataFrame, 
    role: str = "batter", 
    min_pressure_balls: int = 60, 
    min_pressure_matches: int = 5
) -> pd.DataFrame:
    """
    Identifies players satisfying pre-registered eligibility criteria on pressure balls.
    """
    id_col = "striker_id" if role == "batter" else "bowler_id"
    name_col = "striker_name_clean" if role == "batter" else "bowler_name_clean"
    
    p_df = deliv_df[deliv_df["is_pressure"]]
    
    stats = p_df.groupby([id_col, name_col]).agg(
        pressure_deliveries=("pressure_score", "count"),
        pressure_matches=("match_id", "nunique"),
        scopes_present=("competition_scope", lambda s: list(set(s)))
    ).reset_index()
    
    stats["league_evidence"] = stats["scopes_present"].apply(
        lambda sc: "IPL + T20I" if len(sc) > 1 else f"{sc[0]} Only"
    )
    
    eligible = stats[
        (stats["pressure_deliveries"] >= min_pressure_balls) & 
        (stats["pressure_matches"] >= min_pressure_matches)
    ].copy()
    
    eligible = eligible.rename(columns={id_col: "player_id", name_col: "player_name"})
    return eligible.drop(columns=["scopes_present"])
