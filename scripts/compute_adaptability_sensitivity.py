#!/usr/bin/env python3
"""
scripts/compute_adaptability_sensitivity.py
Computes exact sensitivity tables for CPRI component weights (+/-5 pts)
and Adaptability formulation variations using official Phase 8 data.
"""
import pandas as pd
from pathlib import Path

phase8_dir = Path("output/phase8_ranking_reconsideration")
bat_df = pd.read_csv(phase8_dir / "official_top10_batters.csv")
bowl_df = pd.read_csv(phase8_dir / "official_top10_bowlers.csv")
bat_comp = pd.read_csv(phase8_dir / "batter_candidate_comparison.csv")
bowl_comp = pd.read_csv(phase8_dir / "bowler_candidate_comparison.csv")

def evaluate_cohort(df, comp_df, role_name):
    print(f"\n=================== {role_name.upper()} SENSITIVITY ===================")
    merged = pd.merge(df, comp_df[["player_id", "raw_adaptability_delta", "calibrated_adaptability"]], on="player_id")
    rows = []
    for _, r in merged.iterrows():
        name = r["player_name"]
        pi = float(r["score_pressure_impact"])
        pa = float(r["score_adaptability"])
        cc = float(r["score_consistency"])
        rc = float(r["score_reliability"])
        base = float(r["cpri_score"])
        raw_delta = float(r["raw_adaptability_delta"])
        cal_adapt = float(r["calibrated_adaptability"])

        # Weight variations (+/- 5 points)
        # 1. Base: 40/25/20/15
        # 2. Impact-Heavy: 45/20/20/15
        var_impact = 0.45 * pi + 0.20 * pa + 0.20 * cc + 0.15 * rc
        # 3. Adaptability-Heavy: 35/30/20/15
        var_adapt = 0.35 * pi + 0.30 * pa + 0.20 * cc + 0.15 * rc
        # 4. Consistency-Heavy: 35/25/25/15
        var_cons = 0.35 * pi + 0.25 * pa + 0.25 * cc + 0.15 * rc
        # 5. Reliability-Heavy: 35/25/20/20
        var_rel = 0.35 * pi + 0.25 * pa + 0.20 * cc + 0.20 * rc

        rows.append({
            "Rank": int(r["official_rank"]),
            "Player": name,
            "Base_CPRI": round(base, 2),
            "Impact_45": round(var_impact, 2),
            "Adapt_30": round(var_adapt, 2),
            "Cons_25": round(var_cons, 2),
            "Rel_20": round(var_rel, 2),
            "Raw_Delta": round(raw_delta, 2),
            "Cal_PA": round(cal_adapt, 2)
        })
    res_df = pd.DataFrame(rows)
    print(res_df.to_string(index=False))
    return res_df

bat_res = evaluate_cohort(bat_df, bat_comp, "Batter")
bowl_res = evaluate_cohort(bowl_df, bowl_comp, "Bowler")
