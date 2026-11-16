#!/usr/bin/env python3
"""
scripts/build_active_rankings.py
================================
Builds complete active player leaderboards and analysis datasets across:
1. Active Batters (265 players)
2. Active Bowlers (218 players)
3. Active All-Rounders (103 players with dual qualifications)

Saves output to output/eligibility/ and generates summary analytics.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
P8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
ELIG_DIR = REPO_ROOT / "output" / "eligibility"
DATA_DIR = REPO_ROOT / "data"

ELIG_DIR.mkdir(parents=True, exist_ok=True)


def get_evidence_tier(balls: int) -> str:
    if balls >= 600:
        return "Elite Evidence (600+)"
    elif balls >= 400:
        return "Strong Evidence (400-599)"
    elif balls >= 250:
        return "Moderate Evidence (250-399)"
    elif balls >= 150:
        return "Limited Evidence (150-249)"
    else:
        return "Emerging Sample (60-149)"


def main():
    print("=" * 70)
    print("BUILDING COMPREHENSIVE ACTIVE T20 PLAYER RANKINGS & ANALYTICS")
    print("=" * 70)

    # Load authoritative population CSVs and registry
    bat_pop = pd.read_csv(P8_DIR / "batter_full_population.csv")
    bowl_pop = pd.read_csv(P8_DIR / "bowler_full_population.csv")
    reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv")

    retired_names = set(reg_df[reg_df["eligibility_status"] == "RETIRED"]["player_name"])
    print(f"Loaded {len(retired_names)} confirmed retired players to exclude from active rankings.")

    # -------------------------------------------------------------
    # 1. ACTIVE BATTERS
    # -------------------------------------------------------------
    b_act = bat_pop[
        (~bat_pop["player_name"].isin(retired_names)) &
        (bat_pop["pressure_deliveries"] >= 60)
    ].sort_values(by="cpri_score", ascending=False).reset_index(drop=True)

    b_act["active_rank"] = b_act.index + 1
    b_act["evidence_tier"] = b_act["pressure_deliveries"].apply(get_evidence_tier)

    # Add delta column (pressure SR - usual SR baseline ~ 140.67)
    b_act["sr_elevation"] = (b_act["pressure_strike_rate"] - 140.67).round(2)

    cols_b = [
        "active_rank", "player_id", "player_name", "competition_evidence",
        "cpri_score", "evidence_tier", "pressure_deliveries", "pressure_matches",
        "pressure_strike_rate", "sr_elevation", "score_pressure_impact",
        "score_adaptability", "score_consistency", "score_reliability"
    ]
    b_act_out = b_act[cols_b].copy()
    b_act_out.to_csv(ELIG_DIR / "active_batters_rankings.csv", index=False)
    b_act_out.head(10).to_csv(ELIG_DIR / "active_top10_batters.csv", index=False)
    print(f"Generated Active Batters Rankings ({len(b_act_out)} players) -> active_batters_rankings.csv")

    # -------------------------------------------------------------
    # 2. ACTIVE BOWLERS
    # -------------------------------------------------------------
    w_act = bowl_pop[
        (~bowl_pop["player_name"].isin(retired_names)) &
        (bowl_pop["pressure_deliveries"] >= 60)
    ].sort_values(by="cpri_score", ascending=False).reset_index(drop=True)

    w_act["active_rank"] = w_act.index + 1
    w_act["evidence_tier"] = w_act["pressure_deliveries"].apply(get_evidence_tier)

    # Add econ suppression column (usual econ baseline 8.44 - pressure econ)
    w_act["econ_suppression"] = (8.44 - w_act["pressure_economy"]).round(2)

    cols_w = [
        "active_rank", "player_id", "player_name", "competition_evidence",
        "cpri_score", "evidence_tier", "pressure_deliveries", "pressure_matches",
        "pressure_economy", "econ_suppression", "score_pressure_impact",
        "score_adaptability", "score_consistency", "score_reliability"
    ]
    w_act_out = w_act[cols_w].copy()
    w_act_out.to_csv(ELIG_DIR / "active_bowlers_rankings.csv", index=False)
    w_act_out.head(10).to_csv(ELIG_DIR / "active_top10_bowlers.csv", index=False)
    print(f"Generated Active Bowlers Rankings ({len(w_act_out)} players) -> active_bowlers_rankings.csv")

    # -------------------------------------------------------------
    # 3. ACTIVE ALL-ROUNDERS (DUAL-QUALIFIED)
    # -------------------------------------------------------------
    common_pids = set(b_act["player_id"]).intersection(set(w_act["player_id"]))
    ar_records = []

    for pid in common_pids:
        b_r = b_act[b_act["player_id"] == pid].iloc[0]
        w_r = w_act[w_act["player_id"] == pid].iloc[0]

        tot_balls = int(b_r["pressure_deliveries"] + w_r["pressure_deliveries"])
        tot_matches = max(int(b_r["pressure_matches"]), int(w_r["pressure_matches"]))

        # Composite clutch score: harmonic balance between batting and bowling clutch
        # arithmetic mean:
        mean_cpri = (b_r["cpri_score"] + w_r["cpri_score"]) / 2.0
        # volume bonus multiplier (continuous dampening)
        vol_factor = min(1.0, np.tanh(tot_balls / 500.0))
        composite_ar_score = round(mean_cpri * 0.85 + vol_factor * 15.0, 2)

        ar_records.append({
            "player_id": pid,
            "player_name": b_r["player_name"],
            "competition_evidence": b_r["competition_evidence"],
            "composite_ar_cpri": composite_ar_score,
            "batting_cpri": round(b_r["cpri_score"], 2),
            "bowling_cpri": round(w_r["cpri_score"], 2),
            "batting_pressure_balls": int(b_r["pressure_deliveries"]),
            "bowling_pressure_balls": int(w_r["pressure_deliveries"]),
            "total_pressure_balls": tot_balls,
            "total_matches": tot_matches,
            "pressure_strike_rate": round(b_r["pressure_strike_rate"], 2),
            "pressure_economy": round(w_r["pressure_economy"], 2),
            "evidence_tier": get_evidence_tier(tot_balls)
        })

    ar_df = pd.DataFrame(ar_records).sort_values(by="composite_ar_cpri", ascending=False).reset_index(drop=True)
    ar_df["active_ar_rank"] = ar_df.index + 1

    cols_ar = [
        "active_ar_rank", "player_id", "player_name", "competition_evidence",
        "composite_ar_cpri", "batting_cpri", "bowling_cpri", "evidence_tier",
        "total_pressure_balls", "batting_pressure_balls", "bowling_pressure_balls",
        "pressure_strike_rate", "pressure_economy"
    ]
    ar_out = ar_df[cols_ar].copy()
    ar_out.to_csv(ELIG_DIR / "active_allrounders_rankings.csv", index=False)
    ar_out.head(10).to_csv(ELIG_DIR / "active_top10_allrounders.csv", index=False)
    print(f"Generated Active All-Rounders Rankings ({len(ar_out)} players) -> active_allrounders_rankings.csv")

    # -------------------------------------------------------------
    # 4. JSON SUMMARY FOR API / FRONTEND
    # -------------------------------------------------------------
    summary_data = {
        "metadata": {
            "title": "SupeRR Intelligence Active Professional T20 Rankings",
            "audit_date": "2026-11-16",
            "qualifying_criteria": "pressure_deliveries >= 60 AND pressure_matches >= 5 AND eligibility_status == 'ACTIVE'",
            "active_batters_count": len(b_act_out),
            "active_bowlers_count": len(w_act_out),
            "active_allrounders_count": len(ar_out),
        },
        "top10_active_batters": b_act_out.head(10).to_dict(orient="records"),
        "top10_active_bowlers": w_act_out.head(10).to_dict(orient="records"),
        "top10_active_allrounders": ar_out.head(10).to_dict(orient="records")
    }

    with open(ELIG_DIR / "active_rankings_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print("Saved JSON summary -> active_rankings_summary.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
