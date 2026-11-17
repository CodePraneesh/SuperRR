#!/usr/bin/env python3
"""
scripts/build_official_store.py
SupeRR Intelligence - Official Scouting Store Builder (Phase 8 + High-Volume PPR Upgrade)

Builds the official unified competition scouting store:
- output/phase4/data/official_scouting_store.json

Consolidates:
1. official_top10_batters.csv
2. official_top10_bowlers.csv
3. batter_rank_uncertainty.csv
4. bowler_rank_uncertainty.csv
5. batter_candidate_comparison.csv
6. bowler_candidate_comparison.csv
7. batter_full_population.csv / bowler_full_population.csv
8. batter_delivery_expectations.csv / bowler_delivery_expectations.csv
9. Contextual splits from player_contextual_splits.json

Enforces:
- Exact Phase 8 rankings, scores, and components preserved for transparency.
- Pressure Performance Reliability (PPR) scores and Evidence Tiers.
- Volume-Adjusted CPRI (Adjusted CPRI) with empirical Bayes shrinkage.
- Partitioned Main Leaderboard (>= 400 pressure balls) vs Contender / Emerging pool (150-399 balls).
- 90% Rank Confidence Intervals for both official and adjusted ranks.
"""
import os
import sys
import json
import argparse
import datetime
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.ppr_engine import (
    EvidenceTierConfig,
    DEFAULT_EVIDENCE_CONFIG,
    compute_batter_role_metrics,
    compute_bowler_role_metrics,
    enrich_player_with_ppr_and_adjustment,
)

PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
PHASE2_DIR = REPO_ROOT / "output" / "phase2"
PHASE11_DIR = REPO_ROOT / "output" / "phase11_v2"
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
    if reliability_score >= 75.0 and ci_width <= 65 and pressure_deliveries >= 300:
        return "High Confidence"
    return "Exploratory"


def compute_adjusted_rank_cis(items: list, n_boot: int = 500) -> None:
    """Compute 90% bootstrap rank confidence intervals for items ordered by adjusted_cpri."""
    if not items:
        return
    scores = np.array([float(it["adjusted_cpri"]) for it in items])
    balls = np.array([max(1, int(it["pressure_stats"]["pressure_deliveries"])) for it in items])
    sigmas = 12.0 / np.sqrt(balls / 100.0)

    np.random.seed(42)
    boot_ranks = np.zeros((n_boot, len(scores)))
    for b in range(n_boot):
        sim = scores + np.random.normal(0, sigmas)
        order = np.argsort(-sim)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(scores) + 1)
        boot_ranks[b] = ranks

    p5 = np.percentile(boot_ranks, 5, axis=0).astype(int)
    p95 = np.percentile(boot_ranks, 95, axis=0).astype(int)

    for i, it in enumerate(items):
        it["adjusted_rank_ci"] = f"[{p5[i]}, {p95[i]}]"


def load_last_played_lookup():
    """Load player last_played dates from Phase 12 active datasets and data fallbacks."""
    last_played_map = {}
    for fn in ["active_top25_batters.csv", "active_top25_bowlers.csv", "active_top10_batters.csv", "active_top10_bowlers.csv"]:
        fpath = REPO_ROOT / "output" / "phase12_active" / fn
        if fpath.exists():
            df = pd.read_csv(fpath)
            for _, r in df.iterrows():
                if "player_id" in r and pd.notnull(r["player_id"]):
                    last_played_map[int(r["player_id"])] = str(r["last_played"])
                if "player_name" in r and pd.notnull(r["player_name"]):
                    last_played_map[str(r["player_name"])] = str(r["last_played"])

    fallbacks = {
        796: "2024-04-10",  # Matthew Wade
        "Matthew Wade": "2024-04-10",
        143: "2024-05-22",  # Dinesh Karthik
        "Dinesh Karthik": "2024-05-22",
        2756: "2026-05-17", # Shashank Singh
        "Shashank Singh": "2026-05-17",
        5979: "2026-10-11", # Abrar Ahmed
        "Abrar Ahmed": "2026-10-11",
        2878: "2025-05-24", # Mohit Sharma
        "Mohit Sharma": "2025-05-24",
    }
    for k, v in fallbacks.items():
        if k not in last_played_map:
            last_played_map[k] = v
    return last_played_map


def enrich_batter_roster(df, unc_map, comp_map, metrics_map, contextual_splits, lp_map, is_official=True):
    roster = []
    for _, row in df.iterrows():
        pid = int(row["player_id"])
        unc = unc_map.get(pid, {})
        comp = comp_map.get(pid, {})

        rank_p5 = int(unc.get("rank_p5", row["official_rank"]))
        rank_p95 = int(unc.get("rank_p95", row["official_rank"]))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])

        tier = determine_confidence_tier(rel_score, ci_width, p_balls)

        sr = float(row["pressure_strike_rate"])
        if sr >= 165.0:
            classification = "Elite Clutch Accelerant"
        elif sr >= 150.0:
            classification = "Clutch Accelerant"
        else:
            classification = "High-Leverage Anchor"

        splits_entry = contextual_splits.get(row["player_name"], {})

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
            "is_official_top10": is_official,
            "last_played": lp_map.get(pid) or lp_map.get(row["player_name"]) or "2026-11-01",
            "contextual_splits": splits_entry
        }

        batter_dict = enrich_player_with_ppr_and_adjustment(
            batter_dict,
            role="Batter",
            delivery_metrics=metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        roster.append(batter_dict)
    return roster


def enrich_bowler_roster(df, unc_map, comp_map, metrics_map, contextual_splits, lp_map, is_official=True):
    roster = []
    for _, row in df.iterrows():
        pid = int(row["player_id"])
        unc = unc_map.get(pid, {})
        comp = comp_map.get(pid, {})

        rank_p5 = int(unc.get("rank_p5", row["official_rank"]))
        rank_p95 = int(unc.get("rank_p95", row["official_rank"]))
        ci_width = rank_p95 - rank_p5
        rel_score = float(row["score_reliability"])
        p_balls = int(row["pressure_deliveries"])

        tier = determine_confidence_tier(rel_score, ci_width, p_balls)

        econ = float(row["pressure_economy"])
        if econ <= 6.5:
            classification = "Lockdown Clutch Specialist"
        elif econ <= 7.2:
            classification = "High-Leverage Restrictor"
        else:
            classification = "Clutch Wicket-Taker"

        splits_entry = contextual_splits.get(row["player_name"], {})

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
            "is_official_top10": is_official,
            "last_played": lp_map.get(pid) or lp_map.get(row["player_name"]) or "2026-11-01",
            "contextual_splits": splits_entry
        }

        bowler_dict = enrich_player_with_ppr_and_adjustment(
            bowler_dict,
            role="Bowler",
            delivery_metrics=metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        roster.append(bowler_dict)
    return roster


def build_store():
    print("=" * 70)
    print("BUILDING AUTHORITATIVE SCOUTING STORE (PHASE 8 + HIGH-VOLUME UPGRADE)")
    print("=" * 70)

    lp_map = load_last_played_lookup()

    # 1. Load official rosters (Phase 13 Evidence Floor >= 250 balls by default, falling back to Phase 8)
    p13_dir = REPO_ROOT / "output" / "phase13_evidence_floor"
    if p13_dir.exists() and (p13_dir / "official_top10_batters.csv").exists():
        print("  Loading Official Phase 13 Evidence Floor (>= 250 balls) rosters...")
        bat_top10_df = pd.read_csv(p13_dir / "official_top10_batters.csv")
        bowl_top10_df = pd.read_csv(p13_dir / "official_top10_bowlers.csv")
        bat_unc_df = pd.read_csv(p13_dir / "batter_rank_uncertainty.csv")
        bowl_unc_df = pd.read_csv(p13_dir / "bowler_rank_uncertainty.csv")
        bat_comp_df = pd.read_csv(p13_dir / "batter_candidate_comparison.csv")
        bowl_comp_df = pd.read_csv(p13_dir / "bowler_candidate_comparison.csv")
    else:
        print("  Loading Official Phase 8 rosters...")
        bat_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_batters.csv")
        bowl_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_bowlers.csv")
        bat_unc_df = pd.read_csv(PHASE8_DIR / "batter_rank_uncertainty.csv")
        bowl_unc_df = pd.read_csv(PHASE8_DIR / "bowler_rank_uncertainty.csv")
        bat_comp_df = pd.read_csv(PHASE8_DIR / "batter_candidate_comparison.csv")
        bowl_comp_df = pd.read_csv(PHASE8_DIR / "bowler_candidate_comparison.csv")
    bat_pop_df = pd.read_csv(PHASE8_DIR / "batter_full_population.csv")
    bowl_pop_df = pd.read_csv(PHASE8_DIR / "bowler_full_population.csv")

    # Load Pre-Floor Phase 8 rosters and uncertainty for supplementary view
    pre_floor_bat_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_batters.csv")
    pre_floor_bowl_top10_df = pd.read_csv(PHASE8_DIR / "official_top10_bowlers.csv")
    p8_bat_unc_df = pd.read_csv(PHASE8_DIR / "batter_rank_uncertainty.csv")
    p8_bowl_unc_df = pd.read_csv(PHASE8_DIR / "bowler_rank_uncertainty.csv")
    p8_bat_comp_df = pd.read_csv(PHASE8_DIR / "batter_candidate_comparison.csv")
    p8_bowl_comp_df = pd.read_csv(PHASE8_DIR / "bowler_candidate_comparison.csv")

    p8_bat_unc_map = {int(r["player_id"]): r.to_dict() for _, r in p8_bat_unc_df.iterrows()}
    p8_bowl_unc_map = {int(r["player_id"]): r.to_dict() for _, r in p8_bowl_unc_df.iterrows()}
    p8_bat_comp_map = {int(r["player_id"]): r.to_dict() for _, r in p8_bat_comp_df.iterrows()}
    p8_bowl_comp_map = {int(r["player_id"]): r.to_dict() for _, r in p8_bowl_comp_df.iterrows()}

    contextual_splits_by_name = load_contextual_splits()

    bat_unc_map = {int(r["player_id"]): r.to_dict() for _, r in bat_unc_df.iterrows()}
    bowl_unc_map = {int(r["player_id"]): r.to_dict() for _, r in bowl_unc_df.iterrows()}

    bat_comp_map = {int(r["player_id"]): r.to_dict() for _, r in bat_comp_df.iterrows()}
    bowl_comp_map = {int(r["player_id"]): r.to_dict() for _, r in bowl_comp_df.iterrows()}

    # 2. Compute delivery-level granular role metrics
    print("\n[Step 1] Aggregating granular pressure delivery expectations...")
    del_b_path = PHASE2_DIR / "batter_delivery_expectations.csv"
    del_bw_path = PHASE2_DIR / "bowler_delivery_expectations.csv"

    if del_b_path.exists():
        del_b_df = pd.read_csv(del_b_path)
        bat_del_metrics = compute_batter_role_metrics(del_b_df)
        bat_metrics_map = {int(r["striker_id"]): r.to_dict() for _, r in bat_del_metrics.iterrows()}
        print(f"  Processed {len(bat_del_metrics)} batters with delivery-level expectation data.")
    else:
        print("  Warning: batter_delivery_expectations.csv not found, using profile fallbacks.")
        bat_metrics_map = {}

    if del_bw_path.exists():
        del_bw_df = pd.read_csv(del_bw_path)
        bowl_del_metrics = compute_bowler_role_metrics(del_bw_df)
        bowl_metrics_map = {int(r["bowler_id"]): r.to_dict() for _, r in bowl_del_metrics.iterrows()}
        print(f"  Processed {len(bowl_del_metrics)} bowlers with delivery-level expectation data.")
    else:
        print("  Warning: bowler_delivery_expectations.csv not found, using profile fallbacks.")
        bowl_metrics_map = {}

    # 3. Build Official Top 10 Batters
    print("\n[Step 2] Enriching Official Top 10 Batters...")
    official_batters = enrich_batter_roster(
        bat_top10_df,
        bat_unc_map,
        bat_comp_map,
        bat_metrics_map,
        contextual_splits_by_name,
        lp_map,
        is_official=True
    )

    # 4. Build Official Top 10 Bowlers
    print("\n[Step 3] Enriching Official Top 10 Bowlers...")
    official_bowlers = enrich_bowler_roster(
        bowl_top10_df,
        bowl_unc_map,
        bowl_comp_map,
        bowl_metrics_map,
        contextual_splits_by_name,
        lp_map,
        is_official=True
    )

    # 4b. Build Enriched Pre-Floor Phase 8 Baseline Rosters (Supplementary)
    print("\n[Step 3b] Enriching Pre-Floor Phase 8 Baseline Rosters...")
    pre_floor_batters = enrich_batter_roster(
        pre_floor_bat_top10_df,
        p8_bat_unc_map,
        p8_bat_comp_map,
        bat_metrics_map,
        contextual_splits_by_name,
        lp_map,
        is_official=True
    )
    pre_floor_bowlers = enrich_bowler_roster(
        pre_floor_bowl_top10_df,
        p8_bowl_unc_map,
        p8_bowl_comp_map,
        bowl_metrics_map,
        contextual_splits_by_name,
        lp_map,
        is_official=True
    )

    # 5. Build Candidate Batters (Ranks 11-25)
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

        b_cand = {
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
            "last_played": lp_map.get(pid) or lp_map.get(row["player_name"]) or "2026-11-01",
            "contextual_splits": splits_entry
        }

        b_cand = enrich_player_with_ppr_and_adjustment(
            b_cand,
            role="Batter",
            delivery_metrics=bat_metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        candidate_batters.append(b_cand)

    # 6. Build Candidate Bowlers (Ranks 11-25)
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

        bw_cand = {
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
            "last_played": lp_map.get(pid) or lp_map.get(row["player_name"]) or "2026-11-01",
            "contextual_splits": splits_entry
        }

        bw_cand = enrich_player_with_ppr_and_adjustment(
            bw_cand,
            role="Bowler",
            delivery_metrics=bowl_metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        candidate_bowlers.append(bw_cand)

    # 7. Helper: Add all eligible players from population (e.g. >= 400 balls outside top 25)
    existing_bat_ids = {p["player_id"] for p in official_batters + candidate_batters}
    additional_batters = []
    for _, row in bat_pop_df.iterrows():
        pid = int(row["player_id"])
        if pid in existing_bat_ids:
            continue
        p_balls = int(row["pressure_deliveries"])
        if p_balls < 150:
            continue  # ignore unranked insufficient evidence
        sr = float(row["pressure_strike_rate"])
        classification = "Elite Clutch Accelerant" if sr >= 165 else "Clutch Accelerant" if sr >= 150 else "High-Leverage Anchor"
        tier = "High Confidence" if row["score_reliability"] >= 75.0 and p_balls >= 300 else "Exploratory"
        splits_entry = contextual_splits_by_name.get(row["player_name"], {})
        rank_val = 999 if pd.isna(row.get("official_rank")) else int(row["official_rank"])

        b_item = {
            "official_rank": rank_val,
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Batter",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(float(row["score_reliability"]), 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_strike_rate": round(sr, 2),
                "pressure_run_res": round(float(row["pressure_run_res"]), 2),
                "pressure_surv_res": round(float(row["pressure_surv_res"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(row.get("total_deliveries", p_balls)),
                "total_matches": int(row.get("total_matches", row["pressure_matches"]))
            },
            "rank_uncertainty": {
                "rank_p5": rank_val,
                "rank_p95": rank_val + 25,
                "median_rank": rank_val,
                "rank_std": 15.0,
                "top10_inclusion_freq": 0.0,
                "ci_display": f"[{rank_val}, {rank_val + 25}]"
            },
            "confidence_tier": tier,
            "tactical_classification": classification,
            "is_official_top10": False,
            "contextual_splits": splits_entry
        }
        b_item = enrich_player_with_ppr_and_adjustment(
            b_item,
            role="Batter",
            delivery_metrics=bat_metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        additional_batters.append(b_item)

    existing_bowl_ids = {p["player_id"] for p in official_bowlers + candidate_bowlers}
    additional_bowlers = []
    for _, row in bowl_pop_df.iterrows():
        pid = int(row["player_id"])
        if pid in existing_bowl_ids:
            continue
        p_balls = int(row["pressure_deliveries"])
        if p_balls < 150:
            continue
        econ = float(row["pressure_economy"])
        classification = "Lockdown Clutch Specialist" if econ <= 6.5 else "High-Leverage Restrictor" if econ <= 7.2 else "Clutch Wicket-Taker"
        tier = "High Confidence" if row["score_reliability"] >= 75.0 and p_balls >= 300 else "Exploratory"
        splits_entry = contextual_splits_by_name.get(row["player_name"], {})
        rank_val = 999 if pd.isna(row.get("official_rank")) else int(row["official_rank"])

        bw_item = {
            "official_rank": rank_val,
            "player_id": pid,
            "player_name": row["player_name"],
            "role": "Bowler",
            "competition_evidence": row["competition_evidence"],
            "cpri_score": round(float(row["cpri_score"]), 2),
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(float(row["score_reliability"]), 2),
            },
            "pressure_stats": {
                "pressure_deliveries": p_balls,
                "pressure_matches": int(row["pressure_matches"]),
                "pressure_economy": round(econ, 2),
                "pressure_strike_rate": round(float(row["pressure_strike_rate"]), 2),
                "pressure_runs_saved": round(float(row["pressure_runs_saved"]), 2),
                "pressure_wkts_above_exp": round(float(row["pressure_wkts_above_exp"]), 2),
                "pressure_wpa": round(float(row["pressure_wpa"]), 4),
                "total_deliveries": int(row.get("total_deliveries", p_balls)),
                "total_matches": int(row.get("total_matches", row["pressure_matches"]))
            },
            "rank_uncertainty": {
                "rank_p5": rank_val,
                "rank_p95": rank_val + 25,
                "median_rank": rank_val,
                "rank_std": 15.0,
                "top10_inclusion_freq": 0.0,
                "ci_display": f"[{rank_val}, {rank_val + 25}]"
            },
            "confidence_tier": tier,
            "tactical_classification": classification,
            "is_official_top10": False,
            "contextual_splits": splits_entry
        }
        bw_item = enrich_player_with_ppr_and_adjustment(
            bw_item,
            role="Bowler",
            delivery_metrics=bowl_metrics_map.get(pid),
            config=DEFAULT_EVIDENCE_CONFIG
        )
        additional_bowlers.append(bw_item)

    all_batters = official_batters + candidate_batters + additional_batters
    all_bowlers = official_bowlers + candidate_bowlers + additional_bowlers

    # 8. Partition into Main Leaderboard (>= 400 balls) and Contenders (150-399 balls)
    print("\n[Step 4] Partitioning into Main Leaderboard and Contenders...")
    main_batters = [p for p in all_batters if p["is_main_eligible"]]
    main_batters.sort(key=lambda p: p["adjusted_cpri"], reverse=True)
    for rank_idx, p in enumerate(main_batters, 1):
        p["adjusted_rank"] = rank_idx
    compute_adjusted_rank_cis(main_batters)

    contender_batters = [p for p in all_batters if not p["is_main_eligible"] and p["pressure_stats"]["pressure_deliveries"] >= 150]
    contender_batters.sort(key=lambda p: p["adjusted_cpri"], reverse=True)
    for rank_idx, p in enumerate(contender_batters, 1):
        p["adjusted_rank"] = rank_idx
    compute_adjusted_rank_cis(contender_batters)

    main_bowlers = [p for p in all_bowlers if p["is_main_eligible"]]
    main_bowlers.sort(key=lambda p: p["adjusted_cpri"], reverse=True)
    for rank_idx, p in enumerate(main_bowlers, 1):
        p["adjusted_rank"] = rank_idx
    compute_adjusted_rank_cis(main_bowlers)

    contender_bowlers = [p for p in all_bowlers if not p["is_main_eligible"] and p["pressure_stats"]["pressure_deliveries"] >= 150]
    contender_bowlers.sort(key=lambda p: p["adjusted_cpri"], reverse=True)
    for rank_idx, p in enumerate(contender_bowlers, 1):
        p["adjusted_rank"] = rank_idx
    compute_adjusted_rank_cis(contender_bowlers)

    # Combined dictionaries for fast indexing
    combined_pool = all_batters + all_bowlers + pre_floor_batters + pre_floor_bowlers
    by_player_name = {}
    by_player_id = {}
    for p in combined_pool:
        if p["player_name"] not in by_player_name:
            by_player_name[p["player_name"]] = p
        if str(p["player_id"]) not in by_player_id:
            by_player_id[str(p["player_id"])] = p

    # Evidence tier breakdown
    bat_tier_counts = pd.Series([p["evidence_tier"] for p in all_batters]).value_counts().to_dict()
    bowl_tier_counts = pd.Series([p["evidence_tier"] for p in all_bowlers]).value_counts().to_dict()

    store_payload = {
        "version": "CPRI-v1.1.0-HIGH-VOLUME-UPGRADE",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metadata": {
            "description": "Authoritative unified official Top 10 rankings (with uniform >= 250 pressure balls evidence floor) for SupeRR Selector Season 2.",
            "source": "Phase 13 Uniform Minimum-Evidence Floor (>= 250 balls) + Pre-Floor Phase 8 Baseline",
            "floor_rule": "Uniform minimum-evidence floor >= 250 pressure balls in ranked role (post-hoc disclosure)",
            "total_official_batters": len(official_batters),
            "total_official_bowlers": len(official_bowlers),
            "total_pre_floor_batters": len(pre_floor_batters),
            "total_pre_floor_bowlers": len(pre_floor_bowlers),
            "total_candidate_batters": len(candidate_batters),
            "total_candidate_bowlers": len(candidate_bowlers),
            "total_main_eligible_batters": len(main_batters),
            "total_main_eligible_bowlers": len(main_bowlers),
            "total_contender_batters": len(contender_batters),
            "total_contender_bowlers": len(contender_bowlers),
            "evidence_tier_counts_batters": bat_tier_counts,
            "evidence_tier_counts_bowlers": bowl_tier_counts,
        },
        # Official Top 10 arrays (Phase 13: >= 250 balls floor)
        "official_top10_batters": official_batters,
        "official_top10_bowlers": official_bowlers,
        # Preserved Pre-Floor Phase 8 official arrays for supplementary view (enriched)
        "pre_floor_top10_batters": pre_floor_batters,
        "pre_floor_top10_bowlers": pre_floor_bowlers,
        "candidate_batters": candidate_batters,
        "candidate_bowlers": candidate_bowlers,
        # High-Volume Upgraded Leaderboards
        "main_leaderboard_batters": main_batters,
        "main_leaderboard_bowlers": main_bowlers,
        "contender_batters": contender_batters,
        "contender_bowlers": contender_bowlers,
        "by_player_name": by_player_name,
        "by_player_id": by_player_id
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(store_payload, f, indent=2)

    print(f"\nSuccessfully generated upgraded official store at: {OUT_PATH}")
    print(f"  Official Batters (Phase 8): {len(official_batters)}")
    print(f"  Official Bowlers (Phase 8): {len(official_bowlers)}")
    print(f"  Main Leaderboard Batters (>= 400 balls): {len(main_batters)}")
    print(f"  Main Leaderboard Bowlers (>= 400 balls): {len(main_bowlers)}")
    print(f"  Contender Batters (150-399 balls): {len(contender_batters)}")
    print(f"  Contender Bowlers (150-399 balls): {len(contender_bowlers)}")
    print("=" * 70)
    return store_payload


def build_store_v2():
    print("=" * 60)
    print("BUILDING SUPERR INTELLIGENCE V2 SCOUTING STORE")
    print("=" * 60)
    out_v2_path = DATA_DIR / "official_scouting_store_v2.json"

    b_v2_csv = PHASE11_DIR / "official_top10_batters_v2.csv"
    bw_v2_csv = PHASE11_DIR / "official_top10_bowlers_v2.csv"

    if not b_v2_csv.exists() or not bw_v2_csv.exists():
        raise FileNotFoundError(f"v2 CSVs not found in {PHASE11_DIR}. Run `python ml/phase11_v2/run_v2_pipeline.py` first.")

    b_df = pd.read_csv(b_v2_csv)
    bw_df = pd.read_csv(bw_v2_csv)

    official_batters = b_df.to_dict(orient="records")
    official_bowlers = bw_df.to_dict(orient="records")

    store_payload = {
        "version": "CPRI-v2.0.0-ORTHOGONAL-COMPOSITE",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metadata": {
            "description": "Authoritative unified v2 Top 10 batters and bowlers for SupeRR Selector Season 2.",
            "source": "Phase 11 v2 Re-evaluation",
            "total_official_batters": len(official_batters),
            "total_official_bowlers": len(official_bowlers),
        },
        "official_top10_batters": official_batters,
        "official_top10_bowlers": official_bowlers,
    }

    with open(out_v2_path, "w", encoding="utf-8") as f:
        json.dump(store_payload, f, indent=2)

    print(f"Generated v2 official store at: {out_v2_path}")
    print(f"  Official Batters v2: {len(official_batters)}")
    print(f"  Official Bowlers v2: {len(official_bowlers)}")
    print("=" * 60)
    return store_payload


def build_store_active():
    print("=" * 60)
    print("BUILDING SUPERR INTELLIGENCE ACTIVE-ONLY SCOUTING STORE")
    print("=" * 60)
    out_active_path = DATA_DIR / "official_scouting_store_active.json"

    phase12_dir = REPO_ROOT / "output" / "phase12_active"
    b_act_csv = phase12_dir / "active_top10_batters.csv"
    bw_act_csv = phase12_dir / "active_top10_bowlers.csv"

    if not b_act_csv.exists() or not bw_act_csv.exists():
        raise FileNotFoundError(f"Active CSVs not found in {phase12_dir}. Run `python scripts/build_active_view.py` first.")

    b_df = pd.read_csv(b_act_csv)
    bw_df = pd.read_csv(bw_act_csv)

    active_batters = b_df.to_dict(orient="records")
    active_bowlers = bw_df.to_dict(orient="records")

    store_payload = {
        "version": "CPRI-v1.0.0-ACTIVE-12M",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metadata": {
            "description": "Supplementary active-only Top 10 batters and bowlers (last 12 months in data) for SupeRR Selector Season 2.",
            "source": "Phase 12 Active View (12-month recency window)",
            "total_official_batters": len(active_batters),
            "total_official_bowlers": len(active_bowlers),
            "eligibility_rule": ">= 1 ball in supplied data in ranked role on or after 2025-11-01",
        },
        "official_top10_batters": active_batters,
        "official_top10_bowlers": active_bowlers,
    }

    with open(out_active_path, "w", encoding="utf-8") as f:
        json.dump(store_payload, f, indent=2)

    print(f"Generated active official store at: {out_active_path}")
    print(f"  Active Batters (12m): {len(active_batters)}")
    print(f"  Active Bowlers (12m): {len(active_bowlers)}")
    print("=" * 60)
    return store_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build SupeRR Intelligence Scouting Store")
    parser.add_argument("--version", choices=["phase8", "v2", "active"], default="phase8", help="Version to build (default: phase8)")
    args = parser.parse_args()

    if args.version == "v2":
        build_store_v2()
    elif args.version == "active":
        build_store_active()
    else:
        build_store()
