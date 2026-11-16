#!/usr/bin/env python3
"""
scripts/generate_volume_band_analysis.py
========================================
Generates volume-band analysis tables and 400-ball sensitivity tables
for the SupeRR Intelligence methodology report.

POST-HOC ANALYSIS — not pre-registered.
All numbers are derived programmatically from Phase 8 CSVs.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
P8 = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
OUT_DIR = P8  # write JSON alongside the CSVs for easy cross-referencing


def band_label(n: int) -> str:
    if n < 150:
        return "<150"
    elif n < 250:
        return "150-249"
    elif n < 400:
        return "250-399"
    elif n < 600:
        return "400-599"
    else:
        return "600+"


BAND_ORDER = ["<150", "150-249", "250-399", "400-599", "600+"]


def compute_volume_band_table(
    pop_df: pd.DataFrame,
    unc_df: pd.DataFrame,
    role: str,
) -> pd.DataFrame:
    """Return a volume-band summary table for a role (Batters or Bowlers)."""
    df = pop_df.copy()
    unc = unc_df.copy()

    # Merge uncertainty columns
    merge_cols = [c for c in ["player_id", "rank_p5", "rank_p95", "top10_inclusion_freq"] if c in unc.columns]
    df = df.merge(unc[merge_cols], on="player_id", how="left")

    df["band"] = df["pressure_deliveries"].apply(band_label)
    df["ci_width"] = df["rank_p95"] - df["rank_p5"]

    tbl = (
        df.groupby("band", observed=True)
        .agg(
            n_players=("player_id", "count"),
            median_cpri=("cpri_score", "median"),
            max_cpri=("cpri_score", "max"),
            median_ci_width=("ci_width", "median"),
            median_top10_freq=("top10_inclusion_freq", "median"),
        )
        .reindex(BAND_ORDER)
        .reset_index()
        .rename(columns={"band": "Pressure Balls Band"})
    )

    tbl = tbl.round({"median_cpri": 2, "max_cpri": 2, "median_ci_width": 1, "median_top10_freq": 3})

    # Pearson correlation between pressure_deliveries and cpri_score
    corr = df[["pressure_deliveries", "cpri_score"]].dropna().corr().iloc[0, 1]

    print(f"\n{'='*60}")
    print(f"Volume-Band Table — {role}")
    print(f"{'='*60}")
    print(tbl.to_string(index=False))
    print(f"\nPearson r(pressure_balls, CPRI) = {corr:.3f}")

    return tbl, corr


def compute_400_ball_sensitivity(
    bat_pop: pd.DataFrame,
    bowl_pop: pd.DataFrame,
    bat_official: pd.DataFrame,
    bowl_official: pd.DataFrame,
) -> dict:
    """
    Table 1: Top 10 by raw CPRI with >=400 pressure balls (from population CSVs).
    Table 2: For each official Phase 8 player, whether they appear in the 400-ball view.

    POST-HOC sensitivity check; submitted lists remain Phase 8 lists.
    """
    # Table 1 — Batters
    bat400 = (
        bat_pop[bat_pop["pressure_deliveries"] >= 400]
        .nlargest(10, "cpri_score")[["player_name", "pressure_deliveries", "cpri_score"]]
        .reset_index(drop=True)
    )
    bat400.index = bat400.index + 1  # rank 1-10
    bat400.index.name = "400-Ball Rank"

    # Table 1 — Bowlers
    bowl400 = (
        bowl_pop[bowl_pop["pressure_deliveries"] >= 400]
        .nlargest(10, "cpri_score")[["player_name", "pressure_deliveries", "cpri_score"]]
        .reset_index(drop=True)
    )
    bowl400.index = bowl400.index + 1
    bowl400.index.name = "400-Ball Rank"

    # Table 2 — Official players with 400-ball flag
    bat_check = bat_official[["official_rank", "player_name", "pressure_deliveries", "cpri_score"]].copy()
    bat_check["in_400_view"] = bat_check["pressure_deliveries"] >= 400

    bowl_check = bowl_official[["official_rank", "player_name", "pressure_deliveries", "cpri_score"]].copy()
    bowl_check["in_400_view"] = bowl_check["pressure_deliveries"] >= 400

    print(f"\n{'='*60}")
    print("400-Ball Sensitivity — Table 1: Top 10 by Raw CPRI (≥400 balls)")
    print(f"{'='*60}")
    print("Batters:")
    print(bat400.to_string())
    print("\nBowlers:")
    print(bowl400.to_string())

    print(f"\n{'='*60}")
    print("400-Ball Sensitivity — Table 2: Official Phase 8 players — in 400-ball view?")
    print(f"{'='*60}")
    print("Batters:")
    print(bat_check.to_string(index=False))
    print("\nBowlers:")
    print(bowl_check.to_string(index=False))

    return {
        "batter_top10_400": bat400,
        "bowler_top10_400": bowl400,
        "batter_official_check": bat_check,
        "bowler_official_check": bowl_check,
    }


def save_results(
    bat_band_tbl: pd.DataFrame,
    bat_corr: float,
    bowl_band_tbl: pd.DataFrame,
    bowl_corr: float,
    sensitivity: dict,
) -> None:
    """Save all tables to JSON for consumption by report generators."""
    out = {
        "volume_band": {
            "batters": {
                "table": bat_band_tbl.to_dict(orient="records"),
                "corr_pressure_balls_cpri": round(bat_corr, 3),
            },
            "bowlers": {
                "table": bowl_band_tbl.to_dict(orient="records"),
                "corr_pressure_balls_cpri": round(bowl_corr, 3),
            },
        },
        "sensitivity_400": {
            "note": "Post-hoc sensitivity check, not pre-registered; the submitted lists remain the Phase 8 lists.",
            "batter_top10_400": sensitivity["batter_top10_400"].reset_index().to_dict(orient="records"),
            "bowler_top10_400": sensitivity["bowler_top10_400"].reset_index().to_dict(orient="records"),
            "batter_official_check": sensitivity["batter_official_check"].to_dict(orient="records"),
            "bowler_official_check": sensitivity["bowler_official_check"].to_dict(orient="records"),
        },
    }

    out_path = OUT_DIR / "volume_band_analysis.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved volume band analysis JSON → {out_path}")


def main() -> None:
    print("Loading Phase 8 CSVs...")
    bat_pop = pd.read_csv(P8 / "batter_full_population.csv")
    bowl_pop = pd.read_csv(P8 / "bowler_full_population.csv")
    bat_unc = pd.read_csv(P8 / "batter_rank_uncertainty.csv")
    bowl_unc = pd.read_csv(P8 / "bowler_rank_uncertainty.csv")
    bat_official = pd.read_csv(P8 / "official_top10_batters.csv")
    bowl_official = pd.read_csv(P8 / "official_top10_bowlers.csv")

    print(f"Batter population: {len(bat_pop)} rows | Bowler population: {len(bowl_pop)} rows")

    bat_band_tbl, bat_corr = compute_volume_band_table(bat_pop, bat_unc, "Batters")
    bowl_band_tbl, bowl_corr = compute_volume_band_table(bowl_pop, bowl_unc, "Bowlers")

    sensitivity = compute_400_ball_sensitivity(bat_pop, bowl_pop, bat_official, bowl_official)

    save_results(bat_band_tbl, bat_corr, bowl_band_tbl, bowl_corr, sensitivity)

    print("\nDone.")


if __name__ == "__main__":
    main()
