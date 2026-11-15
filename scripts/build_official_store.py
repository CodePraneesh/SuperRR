#!/usr/bin/env python3
"""
scripts/build_official_store.py
SupeRR Intelligence - Official Phase 8 Scouting Store Builder

Builds the official unified competition scouting store:
- output/phase4/data/official_scouting_store.json

Consolidates:
1. official_top10_batters.csv
2. official_top10_bowlers.csv
3. batter_rank_uncertainty.csv
4. bowler_rank_uncertainty.csv
5. batter_candidate_comparison.csv
6. bowler_candidate_comparison.csv
7. Contextual splits from player_contextual_splits.json (if available)

Enforces:
- Exact Phase 8 rankings, scores, and components
- 90% Rank Confidence Intervals [rank_p5, rank_p95]
- Confidence tier classification: "High Confidence" vs "Exploratory"
"""
import os
import sys
import json
import datetime
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
DATA_DIR = REPO_ROOT / "output" / "phase4" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = DATA_DIR / "official_scouting_store.json"


def load_contextual_splits():
    splits_file = DATA_DIR / "player_contextual_splits.json"
    if splits_file.exists():
        try:
            with open(splits_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("by_player_name", {})
        except Exception:
            pass
    return {}


def determine_confidence_tier(reliability_score: float, ci_width: int, pressure_deliveries: int) -> str:
    # High Confidence requires solid sample size and bounded CI width
    if reliability_score >= 75.0 and ci_width <= 65 and pressure_deliveries >= 300:
        return "High Confidence"
    return "Exploratory"


def build_store():
    print("=" * 60)
    print("BUILDING OFFICIAL PHASE 8 SCOUTING STORE")
    print("=" * 60)

    # 1. Load official files
    bat_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_batters.csv")
    bowl_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_bowlers.csv")
    bat_unc_df = pd.read_csv(PHASE8_DIR / "batter_rank_uncertainty.csv")
    bowl_unc_df = pd.read_csv(PHASE8_DIR / "bowler_rank_uncertainty.csv")
    bat_comp_df = pd.read_csv(PHASE8_DIR / "batter_candidate_comparison.csv")
    bowl_comp_df = pd.read_csv(PHASE8_DIR / "bowler_candidate_comparison.csv")

    contextual_splits_by_name = load_contextual_splits()

    bat_unc_map = {int(r["player_id"]): r.to_dict() for _, r in bat_unc_df.iterrows()}
    bowl_unc_map = {int(r["player_id"]): r.to_dict() for _, r in bowl_unc_df.iterrows()}

    bat_comp_map = {int(r["player_id"]): r.to_dict() for _, r in bat_comp_df.iterrows()}
    bowl_comp_map = {int(r["player_id"]): r.to_dict() for _, r in bowl_comp_df.iterrows()}

    # Build Official Batters
    official_batters = []
    for _, row in bat_top10_df.iterrows():
        pid = int(row["player_id"])
        unc = bat_unc_map.get(pid, {})
        comp = bat_comp_map.get(pid, {})

        rank_p5 = int(unc.get("rank_p5", row["official_rank"]))
        rank_p95 = int(unc.get("rank_p95", row["official_rank"]))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])

        tier = determine_confidence_tier(rel_score, ci_width, p_balls)

        # Tactical classification
        sr = float(row["pressure_strike_rate"])
        if sr >= 165.0:
            classification = "Elite Clutch Accelerant"
        elif sr >= 150.0:
            classification = "Clutch Accelerant"
        else:
            classification = "High-Leverage Anchor"

        splits_entry = contextual_splits_by_name.get(row["player_name"], {})

        batter_dict = {
            "official_rank": int(row["official_rank"]),
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Batter",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(rel_score, 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_strike_rate": round(sr, 2),
                "pressure_run_res": round(float(row["pressure_run_res"]), 2),
                "pressure_surv_res": round(float(row["pressure_surv_res"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(comp.get("total_deliveries", p_balls)),
                "total_matches": int(comp.get("total_matches", row["pressure_matches"]))
            },
            "rank_uncertainty": {
                "rank_p5": rank_p5,
                "rank_p95": rank_p95,
                "median_rank": int(unc.get("median_rank", row["official_rank"])),
                "rank_std": round(float(unc.get("rank_std", 0.0)), 2),
                "top10_inclusion_freq": round(float(unc.get("top10_inclusion_freq", 0.0)), 3),
                "ci_display": f"[{rank_p5}, {rank_p95}]"
            },
            "confidence_tier": tier,
            "tactical_classification": classification,
            "is_official_top10": True,
            "contextual_splits": splits_entry
        }
        official_batters.append(batter_dict)

    # Build Official Bowlers
    official_bowlers = []
    for _, row in bowl_top10_df.iterrows():
        pid = int(row["player_id"])
        unc = bowl_unc_map.get(pid, {})
        comp = bowl_comp_map.get(pid, {})

        rank_p5 = int(unc.get("rank_p5", row["official_rank"]))
        rank_p95 = int(unc.get("rank_p95", row["official_rank"]))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])

        tier = determine_confidence_tier(rel_score, ci_width, p_balls)

        # Tactical classification
        econ = float(row["pressure_economy"])
        if econ <= 6.5:
            classification = "Lockdown Clutch Specialist"
        elif econ <= 7.2:
            classification = "High-Leverage Restrictor"
        else:
            classification = "Clutch Wicket-Taker"

        splits_entry = contextual_splits_by_name.get(row["player_name"], {})

        bowler_dict = {
            "official_rank": int(row["official_rank"]),
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Bowler",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(rel_score, 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_economy": round(econ, 2),
                "pressure_strike_rate": round(float(row["pressure_strike_rate"]), 2),
                "pressure_runs_saved": round(float(row["pressure_runs_saved"]), 2),
                "pressure_wkts_above_exp": round(float(row["pressure_wkts_above_exp"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(comp.get("total_deliveries", p_balls)),
                "total_matches": int(comp.get("total_matches", row["pressure_matches"]))
            },
            "rank_uncertainty": {
                "rank_p5": rank_p5,
                "rank_p95": rank_p95,
                "median_rank": int(unc.get("median_rank", row["official_rank"])),
                "rank_std": round(float(unc.get("rank_std", 0.0)), 2),
                "top10_inclusion_freq": round(float(unc.get("top10_inclusion_freq", 0.0)), 3),
                "ci_display": f"[{rank_p5}, {rank_p95}]"
            },
            "confidence_tier": tier,
            "tactical_classification": classification,
            "is_official_top10": True,
            "contextual_splits": splits_entry
        }
        official_bowlers.append(bowler_dict)

    # Build Candidates 11-25 for Batters
    candidate_batters = []
    for _, row in bat_comp_df.iterrows():
        rank = int(row["official_rank"])
        if rank <= 10:
            continue
        pid = int(row["player_id"])
        unc = bat_unc_map.get(pid, {})
        rank_p5 = int(unc.get("rank_p5", rank))
        rank_p95 = int(unc.get("rank_p95", rank))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])
        tier = determine_confidence_tier(rel_score, ci_width, p_balls)
        splits_entry = contextual_splits_by_name.get(row["player_name"], {})

        candidate_batters.append({
            "official_rank": rank,
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Batter",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(rel_score, 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_strike_rate": round(float(row["pressure_strike_rate"]), 2),
                "pressure_run_res": round(float(row["pressure_run_res"]), 2),
                "pressure_surv_res": round(float(row["pressure_surv_res"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(row["total_deliveries"]),
                "total_matches": int(row["total_matches"])
            },
            "rank_uncertainty": {
                "rank_p5": rank_p5,
                "rank_p95": rank_p95,
                "median_rank": int(unc.get("median_rank", rank)),
                "rank_std": round(float(unc.get("rank_std", 0.0)), 2),
                "top10_inclusion_freq": round(float(unc.get("top10_inclusion_freq", 0.0)), 3),
                "ci_display": f"[{rank_p5}, {rank_p95}]"
            },
            "confidence_tier": tier,
            "tactical_classification": "Contender Candidate",
            "is_official_top10": False,
            "contextual_splits": splits_entry
        })

    # Build Candidates 11-25 for Bowlers
    candidate_bowlers = []
    for _, row in bowl_comp_df.iterrows():
        rank = int(row["official_rank"])
        if rank <= 10:
            continue
        pid = int(row["player_id"])
        unc = bowl_unc_map.get(pid, {})
        rank_p5 = int(unc.get("rank_p5", rank))
        rank_p95 = int(unc.get("rank_p95", rank))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])
        tier = determine_confidence_tier(rel_score, ci_width, p_balls)
        splits_entry = contextual_splits_by_name.get(row["player_name"], {})

        candidate_bowlers.append({
            "official_rank": rank,
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Bowler",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(rel_score, 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_economy": round(float(row["pressure_economy"]), 2),
                "pressure_strike_rate": round(float(row["pressure_strike_rate"]), 2),
                "pressure_runs_saved": round(float(row["pressure_runs_saved"]), 2),
                "pressure_wkts_above_exp": round(float(row["pressure_wkts_above_exp"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(row["total_deliveries"]),
                "total_matches": int(row["total_matches"])
            },
            "rank_uncertainty": {
                "rank_p5": rank_p5,
                "rank_p95": rank_p95,
                "median_rank": int(unc.get("median_rank", rank)),
                "rank_std": round(float(unc.get("rank_std", 0.0)), 2),
                "top10_inclusion_freq": round(float(unc.get("top10_inclusion_freq", 0.0)), 3),
                "ci_display": f"[{rank_p5}, {rank_p95}]"
            },
            "confidence_tier": tier,
            "tactical_classification": "Contender Candidate",
            "is_official_top10": False,
            "contextual_splits": splits_entry
        })

    # Combined dictionaries for fast indexing
    all_players = official_batters + official_bowlers + candidate_batters + candidate_bowlers
    by_player_name = {p["player_name"]: p for p in all_players}
    by_player_id = {str(p["player_id"]): p for p in all_players}

    store_payload = {
        "version": "CPRI-v1.0.0-PHASE8-OFFICIAL",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metadata": {
            "description": "Authoritative unified official Top 10 batters and bowlers for SupeRR Selector Season 2.",
            "source": "Phase 8 Official Ranking Reconsideration",
            "total_official_batters": len(official_batters),
            "total_official_bowlers": len(official_bowlers),
            "total_candidate_batters": len(candidate_batters),
            "total_candidate_bowlers": len(candidate_bowlers),
        },
        "official_top10_batters": official_batters,
        "official_top10_bowlers": official_bowlers,
        "candidate_batters": candidate_batters,
        "candidate_bowlers": candidate_bowlers,
        "by_player_name": by_player_name,
        "by_player_id": by_player_id
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(store_payload, f, indent=2)

    print(f"Generated official store at: {OUT_PATH}")
    print(f"  Official Batters: {len(official_batters)}")
    print(f"  Official Bowlers: {len(official_bowlers)}")
    print(f"  Candidate Batters: {len(candidate_batters)}")
    print(f"  Candidate Bowlers: {len(candidate_bowlers)}")
    print("=" * 60)
    return store_payload


if __name__ == "__main__":
    build_store()
