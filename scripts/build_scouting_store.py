#!/usr/bin/env python3
"""
build_scouting_store.py
SupeRR Intelligence - Phase 4.2 Scouting Store Builder

Builds three structured scouting data stores:
1. output/phase4/data/player_scouting_profiles.json
2. output/phase4/data/player_contextual_splits.json
3. output/phase4/data/head_to_head_matrix.json

Strictly adheres to:
- Phase 3.5 Frozen CPRI methodology and official/provisional rankings
- Zero-modification of Phase 1-3.5 assets
- Format separation (IPL and T20I never combined)
- Complete coverage of all 40 Official Top 10 + 20 Provisional Top 5 players
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

# Set working directory to project root
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
DATA_OUT_DIR = BASE_DIR / "output" / "phase4" / "data"
DATA_OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_upstream_data():
    """Load all necessary upstream datasets without modifying any files."""
    print("[Step 1] Loading upstream datasets...")
    t0 = time.time()

    # Phase 3.5 Official Rankings and Uncertainty
    off_csv = pd.read_csv("output/phase3_5/official_rankings.csv")
    with open("output/phase3_5/official_rankings.json", "r") as f:
        off_json = json.load(f)
    unc_df = pd.read_csv("output/phase3_5/eligibility_and_uncertainty.csv")

    # Phase 3.3 Complete Metric Aggregates
    bat_p33 = pd.read_csv("output/phase3_3/all_batter_rankings.csv")
    bowl_p33 = pd.read_csv("output/phase3_3/all_bowler_rankings.csv")

    # Phase 2A Pressure-Scored Deliveries (contains all enriched fields + pressure_score 0-100)
    deliv_path = "output/phase2/pressure_scored_deliveries.csv"
    if not os.path.exists(deliv_path):
        deliv_path = "output/processed/deliveries_enriched.csv"

    deliv_cols = [
        "match_id", "innings", "overid", "over_ball_num", "competition_scope",
        "striker_id", "striker_name_clean", "bowler_id", "bowler_name_clean",
        "innings_phase", "pace_or_spin", "batting_type", "pressure_score",
        "batter_faced_ball", "legal_ball", "batter_runs", "bowler_runs_conceded",
        "derived_four", "derived_six", "bowler_wicket"
    ]
    deliv_df = pd.read_csv(deliv_path, usecols=deliv_cols, low_memory=False)

    print(f"  Loaded upstream datasets in {time.time()-t0:.2f}s:")
    print(f"    - Official Rankings: {len(off_csv)} records")
    print(f"    - Uncertainty Audits: {len(unc_df)} records")
    print(f"    - Deliveries: {len(deliv_df)} rows")
    return off_csv, off_json, unc_df, bat_p33, bowl_p33, deliv_df


def build_player_scouting_profiles(off_csv, unc_df, bat_p33, bowl_p33, deliv_df):
    """
    Build Store 1: player_scouting_profiles.json
    Covers all 40 Official Top 10 + 20 Provisional Top 5 records.
    """
    print("\n[Step 2] Building Store 1: player_scouting_profiles.json...")
    t0 = time.time()

    profiles_list = []
    by_key = {}
    by_player_name = {}
    by_cohort = {
        "IPL Batters": [],
        "T20I Batters": [],
        "IPL Bowlers": [],
        "T20I Bowlers": []
    }

    # Build uncertainty lookup: (cohort, player_name) -> dict
    unc_lookup = {}
    for _, row in unc_df.iterrows():
        unc_lookup[(row["cohort"], row["player_name"])] = row.to_dict()

    for idx, row in off_csv.iterrows():
        pname = row["player_name"]
        scope = row["competition_scope"]
        role = row["role"]
        cohort = row["cohort"]
        ranking_tier = row["ranking_tier"]
        official_rank = int(row["official_rank"])
        cpri_score = float(row["cpri_score"])

        # Match Phase 3.3 detailed aggregates
        p33_source = bat_p33 if role == "Batter" else bowl_p33
        p33_match = p33_source[(p33_source["player_name"] == pname) & (p33_source["competition_scope"] == scope)]
        if len(p33_match) == 0:
            raise ValueError(f"Player {pname} ({scope}, {role}) not found in Phase 3.3 rankings!")

        p33_data = p33_match.iloc[0].to_dict()
        player_id = int(p33_data["player_id"])

        # Compute delivery-level stats from source deliveries
        if role == "Batter":
            p_delivs = deliv_df[(deliv_df["striker_id"] == player_id) & (deliv_df["competition_scope"] == scope)]
            faced = p_delivs[p_delivs["batter_faced_ball"] == 1]
            balls_faced = int(len(faced))
            actual_runs = int(faced["batter_runs"].sum())
            fours = int(faced["derived_four"].sum())
            sixes = int(faced["derived_six"].sum())
            boundary_runs = fours * 4 + sixes * 6
            dismissals = int(faced["bowler_wicket"].sum())
            dot_balls = int((faced["batter_runs"] == 0).sum())

            strike_rate = round((actual_runs / balls_faced * 100.0), 2) if balls_faced > 0 else 0.0
            batting_avg = round((actual_runs / dismissals), 2) if dismissals > 0 else None
            dot_pct = round((dot_balls / balls_faced * 100.0), 1) if balls_faced > 0 else 0.0
            boundary_pct = round(((fours + sixes) / balls_faced * 100.0), 1) if balls_faced > 0 else 0.0

            # Pressure subset
            p_faced = faced[faced["pressure_score"] >= 50.0]
            p_balls = int(len(p_faced))
            p_runs = int(p_faced["batter_runs"].sum())
            p_outs = int(p_faced["bowler_wicket"].sum())
            p_sr = round((p_runs / p_balls * 100.0), 2) if p_balls > 0 else 0.0
            p_avg = round((p_runs / p_outs), 2) if p_outs > 0 else None

            # Non-pressure subset
            np_faced = faced[faced["pressure_score"] < 50.0]
            np_balls = int(len(np_faced))
            np_runs = int(np_faced["batter_runs"].sum())
            np_outs = int(np_faced["bowler_wicket"].sum())
            np_sr = round((np_runs / np_balls * 100.0), 2) if np_balls > 0 else 0.0
            np_avg = round((np_runs / np_outs), 2) if np_outs > 0 else None

            role_stats = {
                "balls_faced": balls_faced,
                "actual_runs": actual_runs,
                "strike_rate": strike_rate,
                "batting_average": batting_avg,
                "dismissals": dismissals,
                "fours": fours,
                "sixes": sixes,
                "boundary_runs": boundary_runs,
                "boundary_percentage": boundary_pct,
                "dot_balls": dot_balls,
                "dot_percentage": dot_pct,
                "pressure_stats": {
                    "pressure_balls_faced": p_balls,
                    "pressure_runs": p_runs,
                    "pressure_strike_rate": p_sr,
                    "pressure_dismissals": p_outs,
                    "pressure_batting_average": p_avg,
                    "pressure_run_residual": round(float(p33_data.get("actual_runs_in_pressure", 0.0) - p33_data.get("expected_runs_in_pressure", 0.0)), 2),
                    "pressure_wpa": round(float(p33_data.get("pressure_wpa", 0.0)), 4),
                    "total_wpa": round(float(p33_data.get("total_wpa", 0.0)), 4)
                },
                "nonpressure_stats": {
                    "nonpressure_balls_faced": np_balls,
                    "nonpressure_runs": np_runs,
                    "nonpressure_strike_rate": np_sr,
                    "nonpressure_dismissals": np_outs,
                    "nonpressure_batting_average": np_avg
                }
            }
        else:
            # Bowler
            p_delivs = deliv_df[(deliv_df["bowler_id"] == player_id) & (deliv_df["competition_scope"] == scope)]
            legal = p_delivs[p_delivs["legal_ball"] == 1]
            balls_bowled = int(len(legal))
            overs_bowled = round(balls_bowled / 6.0, 1)
            runs_conceded = int(legal["bowler_runs_conceded"].sum())
            credited_wickets = int(legal["bowler_wicket"].sum())
            fours_conceded = int(legal["derived_four"].sum())
            sixes_conceded = int(legal["derived_six"].sum())
            dot_balls = int((legal["bowler_runs_conceded"] == 0).sum())

            economy = round((runs_conceded / balls_bowled * 6.0), 2) if balls_bowled > 0 else 0.0
            bowling_avg = round((runs_conceded / credited_wickets), 2) if credited_wickets > 0 else None
            bowling_sr = round((balls_bowled / credited_wickets), 1) if credited_wickets > 0 else None
            dot_pct = round((dot_balls / balls_bowled * 100.0), 1) if balls_bowled > 0 else 0.0
            boundary_pct = round(((fours_conceded + sixes_conceded) / balls_bowled * 100.0), 1) if balls_bowled > 0 else 0.0

            # Pressure subset
            p_legal = legal[legal["pressure_score"] >= 50.0]
            p_balls = int(len(p_legal))
            p_overs = round(p_balls / 6.0, 1)
            p_runs = int(p_legal["bowler_runs_conceded"].sum())
            p_wkts = int(p_legal["bowler_wicket"].sum())
            p_econ = round((p_runs / p_balls * 6.0), 2) if p_balls > 0 else 0.0
            p_avg = round((p_runs / p_wkts), 2) if p_wkts > 0 else None

            # Non-pressure subset
            np_legal = legal[legal["pressure_score"] < 50.0]
            np_balls = int(len(np_legal))
            np_overs = round(np_balls / 6.0, 1)
            np_runs = int(np_legal["bowler_runs_conceded"].sum())
            np_wkts = int(np_legal["bowler_wicket"].sum())
            np_econ = round((np_runs / np_balls * 6.0), 2) if np_balls > 0 else 0.0
            np_avg = round((np_runs / np_wkts), 2) if np_wkts > 0 else None

            role_stats = {
                "balls_bowled": balls_bowled,
                "overs_bowled": overs_bowled,
                "runs_conceded": runs_conceded,
                "credited_wickets": credited_wickets,
                "economy_rate": economy,
                "bowling_average": bowling_avg,
                "bowling_strike_rate": bowling_sr,
                "fours_conceded": fours_conceded,
                "sixes_conceded": sixes_conceded,
                "boundary_percentage": boundary_pct,
                "dot_balls": dot_balls,
                "dot_percentage": dot_pct,
                "pressure_stats": {
                    "pressure_balls_bowled": p_balls,
                    "pressure_overs_bowled": p_overs,
                    "pressure_runs_conceded": p_runs,
                    "pressure_wickets": p_wkts,
                    "pressure_economy": p_econ,
                    "pressure_bowling_average": p_avg,
                    "pressure_run_residual": round(float(p33_data.get("actual_runs_conceded_in_pressure", 0.0) - p33_data.get("expected_runs_conceded_in_pressure", 0.0)), 2),
                    "pressure_wpa": round(float(p33_data.get("pressure_wpa", 0.0)), 4),
                    "total_wpa": round(float(p33_data.get("total_wpa", 0.0)), 4)
                },
                "nonpressure_stats": {
                    "nonpressure_balls_bowled": np_balls,
                    "nonpressure_overs_bowled": np_overs,
                    "nonpressure_runs_conceded": np_runs,
                    "nonpressure_wickets": np_wkts,
                    "nonpressure_economy": np_econ,
                    "nonpressure_bowling_average": np_avg
                }
            }

        # Bootstrap uncertainty (if available from official Phase 3.5 audit)
        unc_info = unc_lookup.get((cohort, pname), None)
        if unc_info is not None:
            bootstrap_uncertainty = {
                "is_audited": True,
                "primary_resampling_standard": str(unc_info.get("primary_resampling_standard", "")),
                "prob_eligibility_pct": float(unc_info["prob_eligibility_pct"]) if pd.notna(unc_info["prob_eligibility_pct"]) else None,
                "prob_rank_1_pct": float(unc_info["prob_rank_1_pct"]) if pd.notna(unc_info["prob_rank_1_pct"]) else None,
                "prob_top10_pct": float(unc_info["prob_top10_pct"]) if pd.notna(unc_info["prob_top10_pct"]) else None,
                "conditional_rank_median": int(unc_info["conditional_rank_median"]) if pd.notna(unc_info["conditional_rank_median"]) else None,
                "conditional_rank_95_interval": str(unc_info.get("conditional_rank_95_interval", "")),
                "conditional_cpri_mean": float(unc_info["conditional_cpri_mean"]) if pd.notna(unc_info["conditional_cpri_mean"]) else None,
                "conditional_cpri_std_dev": float(unc_info["conditional_cpri_std_dev"]) if pd.notna(unc_info["conditional_cpri_std_dev"]) else None,
                "conditional_cpri_95_ci": str(unc_info.get("conditional_cpri_95_ci", "")),
                "mc_standard_error_rank1_pct": float(unc_info["mc_standard_error_rank1_pct"]) if pd.notna(unc_info.get("mc_standard_error_rank1_pct")) else None,
                "mc_standard_error_top10_pct": float(unc_info["mc_standard_error_top10_pct"]) if pd.notna(unc_info.get("mc_standard_error_top10_pct")) else None
            }
        else:
            bootstrap_uncertainty = {
                "is_audited": False,
                "primary_resampling_standard": None,
                "prob_eligibility_pct": None,
                "prob_rank_1_pct": None,
                "prob_top10_pct": None,
                "conditional_rank_median": None,
                "conditional_rank_95_interval": None,
                "conditional_cpri_mean": None,
                "conditional_cpri_std_dev": None,
                "conditional_cpri_95_ci": None,
                "mc_standard_error_rank1_pct": None,
                "mc_standard_error_top10_pct": None,
                "provisional_reason": "Provisional ranking due to sub-threshold pressure sample (<100 balls or <8 matches); excluded from primary bootstrap."
            }

        profile_key = f"{scope}_{role}_{player_id}"
        profile = {
            "profile_key": profile_key,
            "player_id": player_id,
            "player_name": pname,
            "competition_scope": scope,
            "role": role,
            "cohort": cohort,
            "ranking_tier": ranking_tier,
            "official_rank": official_rank,
            "is_official_top10": (ranking_tier == "Official Top 10"),
            "is_provisional_top5": (ranking_tier == "Provisional Top 5"),
            "is_champion": (official_rank == 1 and ranking_tier == "Official Top 10"),
            "cpri_score": cpri_score,
            "components": {
                "pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "pressure_adaptability": round(float(row["score_adaptability"]), 2),
                "clutch_consistency": round(float(row["score_consistency"]), 2),
                "reliability_confidence": round(float(row["score_reliability"]), 2)
            },
            "confidence_tier": str(row["confidence_tier"]),
            "status_reason": str(row["status_reason"]),
            "frozen_cpri_metrics": {
                "cpri_score": cpri_score,
                "score_pressure_impact": round(float(row["score_pressure_impact"]), 2),
                "score_adaptability": round(float(row["score_adaptability"]), 2),
                "score_consistency": round(float(row["score_consistency"]), 2),
                "score_reliability": round(float(row["score_reliability"]), 2),
                "frozen_pressure_deliveries": int(row["pressure_deliveries"]),
                "frozen_total_deliveries": int(row["total_deliveries"]),
                "frozen_pressure_matches": int(row["pressure_matches"]),
                "frozen_confidence_tier": str(row["confidence_tier"]),
                "frozen_official_rank": official_rank,
                "source": "Phase 3.5 Official Freeze (official_rankings.csv)"
            },
            "exposure": {
                "total_deliveries": int(row["total_deliveries"]),
                "pressure_deliveries": int(row["pressure_deliveries"]),
                "pressure_matches": int(row["pressure_matches"]),
                "total_matches": int(p33_data.get("total_matches", 0)),
                "balls_per_match": round(float(p33_data.get("balls_per_match", 0.0)), 2) if "balls_per_match" in p33_data and pd.notna(p33_data["balls_per_match"]) else None,
                "pressure_ratio": round(float(p33_data.get("pressure_ratio", 0.0)), 4),
                "pos_pressure_match_ratio": round(float(p33_data.get("pos_pressure_match_ratio", 0.0)), 4),
                "effective_pressure_sample_size": round(float(p33_data.get("effective_pressure_sample_size", 0.0)), 2),
                "pressure_specific_uncertainty": round(float(p33_data.get("pressure_specific_uncertainty", 0.0)), 2),
                "sample_definition_notes": {
                    "frozen_pressure_deliveries": "Authoritative Phase 3.5 count of all match-state deliveries with pressure_score >= 50.0.",
                    "delivery_derived_balls_faced": "Deliveries where batter actually faced the ball (excludes wides/penalties) for batting rate calculations."
                }
            },
            "performance_stats": role_stats,
            "bootstrap_uncertainty": bootstrap_uncertainty
        }

        profiles_list.append(profile)
        by_key[profile_key] = profile
        if pname not in by_player_name:
            by_player_name[pname] = {}
        by_player_name[pname][scope] = profile
        by_cohort[cohort].append(profile)

    store_1 = {
        "metadata": {
            "store_name": "player_scouting_profiles",
            "version": "1.0.0",
            "description": "Comprehensive scouting profiles for all 40 Official Top 10 and 20 Provisional Top 5 players across IPL and T20I.",
            "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_profiles": len(profiles_list),
            "official_top10_count": sum(1 for p in profiles_list if p["is_official_top10"]),
            "provisional_top5_count": sum(1 for p in profiles_list if p["is_provisional_top5"]),
            "cohort_counts": {k: len(v) for k, v in by_cohort.items()}
        },
        "profiles": profiles_list,
        "by_key": by_key,
        "by_player_name": by_player_name,
        "by_cohort": by_cohort
    }

    out_file = DATA_OUT_DIR / "player_scouting_profiles.json"
    with open(out_file, "w") as f:
        json.dump(store_1, f, indent=2)

    sz_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"  Successfully wrote {len(profiles_list)} profiles to {out_file} ({sz_mb:.2f} MB) in {time.time()-t0:.2f}s")
    return store_1


def build_player_contextual_splits(off_csv, bat_p33, bowl_p33, deliv_df):
    """
    Build Store 2: player_contextual_splits.json
    Computes Powerplay, Middle, Death, Pressure vs Non-Pressure,
    and Matchup (Pace/Spin for batters, RHB/LHB for bowlers) splits for all 60 players.
    """
    print("\n[Step 3] Building Store 2: player_contextual_splits.json...")
    t0 = time.time()

    splits_list = []
    by_key = {}
    by_player_name = {}

    def get_sample_tier(balls, role):
        min_balls = 30 if role == "Batter" else 24
        if balls == 0:
            return "No Sample (0 balls)"
        elif balls < min_balls * 0.5:
            return f"Low Sample ({balls} balls)"
        elif balls < min_balls:
            return f"Moderate Sample ({balls} balls)"
        else:
            return f"Robust Sample ({balls} balls)"

    for idx, row in off_csv.iterrows():
        pname = row["player_name"]
        scope = row["competition_scope"]
        role = row["role"]
        cohort = row["cohort"]

        p33_source = bat_p33 if role == "Batter" else bowl_p33
        p33_match = p33_source[(p33_source["player_name"] == pname) & (p33_source["competition_scope"] == scope)]
        player_id = int(p33_match.iloc[0]["player_id"])
        player_key = f"{scope}_{role}_{player_id}"

        if role == "Batter":
            p_delivs = deliv_df[(deliv_df["striker_id"] == player_id) & (deliv_df["competition_scope"] == scope)]
            faced = p_delivs[p_delivs["batter_faced_ball"] == 1]

            def calc_bat_split(df_subset, split_name):
                n_balls = int(len(df_subset))
                runs = int(df_subset["batter_runs"].sum()) if n_balls > 0 else 0
                fours = int(df_subset["derived_four"].sum()) if n_balls > 0 else 0
                sixes = int(df_subset["derived_six"].sum()) if n_balls > 0 else 0
                outs = int(df_subset["bowler_wicket"].sum()) if n_balls > 0 else 0
                dots = int((df_subset["batter_runs"] == 0).sum()) if n_balls > 0 else 0

                sr = round((runs / n_balls * 100.0), 2) if n_balls > 0 else 0.0
                avg = round((runs / outs), 2) if outs > 0 else None
                dot_pct = round((dots / n_balls * 100.0), 1) if n_balls > 0 else 0.0
                b_pct = round(((fours + sixes) / n_balls * 100.0), 1) if n_balls > 0 else 0.0
                return {
                    "split_name": split_name,
                    "balls_faced": n_balls,
                    "runs_scored": runs,
                    "strike_rate": sr,
                    "batting_average": avg,
                    "dismissals": outs,
                    "fours": fours,
                    "sixes": sixes,
                    "boundary_percentage": b_pct,
                    "dot_balls": dots,
                    "dot_percentage": dot_pct,
                    "sample_tier": get_sample_tier(n_balls, "Batter")
                }

            innings_phase_splits = {
                "powerplay": calc_bat_split(faced[faced["innings_phase"] == "powerplay"], "Powerplay (Overs 1-6)"),
                "middle": calc_bat_split(faced[faced["innings_phase"] == "middle"], "Middle Overs (Overs 7-16)"),
                "death": calc_bat_split(faced[faced["innings_phase"] == "death"], "Death Overs (Overs 17-20)")
            }

            bowling_type_splits = {
                "pace": calc_bat_split(faced[faced["pace_or_spin"] == "Pace"], "Against Pace Bowling"),
                "spin": calc_bat_split(faced[faced["pace_or_spin"] == "Spin"], "Against Spin Bowling")
            }

            high_p = calc_bat_split(faced[faced["pressure_score"] >= 50.0], "High Pressure (PI >= 50)")
            low_p = calc_bat_split(faced[faced["pressure_score"] < 50.0], "Low Pressure (PI < 50)")

            delta_sr = round(high_p["strike_rate"] - low_p["strike_rate"], 2)
            delta_dot_pct = round(high_p["dot_percentage"] - low_p["dot_percentage"], 1)

            if high_p["batting_average"] is not None and low_p["batting_average"] is not None:
                delta_avg = round(high_p["batting_average"] - low_p["batting_average"], 2)
            else:
                delta_avg = None

            if delta_sr >= 5.0:
                classification = "Clutch Accelerant"
            elif delta_sr <= -5.0:
                classification = "Pressure Degrader"
            else:
                classification = "Anchor Stabilizer"

            pressure_contrast = {
                "high_pressure": high_p,
                "low_pressure": low_p,
                "delta_strike_rate": delta_sr,
                "delta_batting_average": delta_avg,
                "delta_dot_percentage": delta_dot_pct,
                "tactical_classification": classification
            }

            player_split_obj = {
                "player_key": player_key,
                "player_id": player_id,
                "player_name": pname,
                "competition_scope": scope,
                "role": role,
                "cohort": cohort,
                "total_balls_evaluated": int(len(faced)),
                "innings_phase_splits": innings_phase_splits,
                "bowling_type_splits": bowling_type_splits,
                "pressure_contrast": pressure_contrast
            }

        else:
            # Bowler
            p_delivs = deliv_df[(deliv_df["bowler_id"] == player_id) & (deliv_df["competition_scope"] == scope)]
            legal = p_delivs[p_delivs["legal_ball"] == 1]

            def calc_bowl_split(df_subset, split_name):
                n_balls = int(len(df_subset))
                overs = round(n_balls / 6.0, 1)
                runs = int(df_subset["bowler_runs_conceded"].sum()) if n_balls > 0 else 0
                wkts = int(df_subset["bowler_wicket"].sum()) if n_balls > 0 else 0
                fours = int(df_subset["derived_four"].sum()) if n_balls > 0 else 0
                sixes = int(df_subset["derived_six"].sum()) if n_balls > 0 else 0
                dots = int((df_subset["bowler_runs_conceded"] == 0).sum()) if n_balls > 0 else 0

                econ = round((runs / n_balls * 6.0), 2) if n_balls > 0 else 0.0
                b_avg = round((runs / wkts), 2) if wkts > 0 else None
                b_sr = round((n_balls / wkts), 1) if wkts > 0 else None
                dot_pct = round((dots / n_balls * 100.0), 1) if n_balls > 0 else 0.0
                b_pct = round(((fours + sixes) / n_balls * 100.0), 1) if n_balls > 0 else 0.0
                return {
                    "split_name": split_name,
                    "balls_bowled": n_balls,
                    "overs_bowled": overs,
                    "runs_conceded": runs,
                    "credited_wickets": wkts,
                    "economy_rate": econ,
                    "bowling_average": b_avg,
                    "bowling_strike_rate": b_sr,
                    "fours_conceded": fours,
                    "sixes_conceded": sixes,
                    "boundary_percentage": b_pct,
                    "dot_balls": dots,
                    "dot_percentage": dot_pct,
                    "sample_tier": get_sample_tier(n_balls, "Bowler")
                }

            innings_phase_splits = {
                "powerplay": calc_bowl_split(legal[legal["innings_phase"] == "powerplay"], "Powerplay (Overs 1-6)"),
                "middle": calc_bowl_split(legal[legal["innings_phase"] == "middle"], "Middle Overs (Overs 7-16)"),
                "death": calc_bowl_split(legal[legal["innings_phase"] == "death"], "Death Overs (Overs 17-20)")
            }

            batter_hand_splits = {
                "rhb": calc_bowl_split(legal[legal["batting_type"] == "RHB"], "Against Right-Hand Batters"),
                "lhb": calc_bowl_split(legal[legal["batting_type"] == "LHB"], "Against Left-Hand Batters")
            }

            high_p = calc_bowl_split(legal[legal["pressure_score"] >= 50.0], "High Pressure (PI >= 50)")
            low_p = calc_bowl_split(legal[legal["pressure_score"] < 50.0], "Low Pressure (PI < 50)")

            delta_econ = round(high_p["economy_rate"] - low_p["economy_rate"], 2)
            delta_dot_pct = round(high_p["dot_percentage"] - low_p["dot_percentage"], 1)

            if high_p["bowling_average"] is not None and low_p["bowling_average"] is not None:
                delta_avg = round(high_p["bowling_average"] - low_p["bowling_average"], 2)
            else:
                delta_avg = None

            # Lower economy in pressure is desirable for a bowler
            if delta_econ <= -0.50:
                classification = "High-Leverage Constrictor"
            elif delta_econ >= 0.50:
                classification = "Pressure Vulnerable"
            else:
                classification = "Steady Executor"

            pressure_contrast = {
                "high_pressure": high_p,
                "low_pressure": low_p,
                "delta_economy": delta_econ,
                "delta_bowling_average": delta_avg,
                "delta_dot_percentage": delta_dot_pct,
                "tactical_classification": classification
            }

            player_split_obj = {
                "player_key": player_key,
                "player_id": player_id,
                "player_name": pname,
                "competition_scope": scope,
                "role": role,
                "cohort": cohort,
                "total_balls_evaluated": int(len(legal)),
                "innings_phase_splits": innings_phase_splits,
                "batter_hand_splits": batter_hand_splits,
                "pressure_contrast": pressure_contrast
            }

        splits_list.append(player_split_obj)
        by_key[player_key] = player_split_obj
        if pname not in by_player_name:
            by_player_name[pname] = {}
        by_player_name[pname][scope] = player_split_obj

    store_2 = {
        "metadata": {
            "store_name": "player_contextual_splits",
            "version": "1.0.0",
            "description": "Contextual phase, bowling style/handedness, and pressure contrast splits for all 60 ranked players.",
            "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_players": len(splits_list),
            "batters_count": sum(1 for s in splits_list if s["role"] == "Batter"),
            "bowlers_count": sum(1 for s in splits_list if s["role"] == "Bowler")
        },
        "splits": splits_list,
        "by_key": by_key,
        "by_player_name": by_player_name
    }

    out_file = DATA_OUT_DIR / "player_contextual_splits.json"
    with open(out_file, "w") as f:
        json.dump(store_2, f, indent=2)

    sz_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"  Successfully wrote {len(splits_list)} player splits to {out_file} ({sz_mb:.2f} MB) in {time.time()-t0:.2f}s")
    return store_2


def build_head_to_head_matrix(off_csv, deliv_df):
    """
    Build Store 3: head_to_head_matrix.json
    Computes all actual batter vs bowler matchups across IPL and T20I.
    Flags sample tiers and highlights matchups involving the 60 ranked players.
    """
    print("\n[Step 4] Building Store 3: head_to_head_matrix.json...")
    t0 = time.time()

    # Identify ranked player IDs to flag matchups involving official/provisional players
    ranked_batter_ids = set()
    ranked_bowler_ids = set()
    for _, row in off_csv.iterrows():
        pname = row["player_name"]
        scope = row["competition_scope"]
        role = row["role"]
        # Find player_id
        if role == "Batter":
            match = deliv_df[(deliv_df["striker_name_clean"] == pname) & (deliv_df["competition_scope"] == scope)]
            if len(match) > 0:
                ranked_batter_ids.add((scope, int(match.iloc[0]["striker_id"])))
        else:
            match = deliv_df[(deliv_df["bowler_name_clean"] == pname) & (deliv_df["competition_scope"] == scope)]
            if len(match) > 0:
                ranked_bowler_ids.add((scope, int(match.iloc[0]["bowler_id"])))

    # Filter deliveries: in-scope format (IPL / T20I) and batter faced legal ball
    ps_in = deliv_df[deliv_df["competition_scope"].isin(["IPL", "T20I"]) & (deliv_df["batter_faced_ball"] == 1)].copy()

    # Aggregate by matchup
    grp = ps_in.groupby(
        ["competition_scope", "striker_id", "striker_name_clean", "bowler_id", "bowler_name_clean"]
    ).agg(
        balls_faced=("batter_faced_ball", "sum"),
        runs_scored=("batter_runs", "sum"),
        fours=("derived_four", "sum"),
        sixes=("derived_six", "sum"),
        dismissals=("bowler_wicket", "sum"),
        dot_balls=("batter_runs", lambda s: int((s == 0).sum())),
        avg_pressure_score=("pressure_score", "mean")
    ).reset_index()

    matchups_list = []
    matchups_by_key = {}
    ranked_matchups = []
    tier_counts = {
        "Very Low Sample (<6 balls)": 0,
        "Low Sample (6-17 balls)": 0,
        "Moderate Sample (18-29 balls)": 0,
        "Robust Sample (>=30 balls)": 0
    }

    for _, row in grp.iterrows():
        scope = str(row["competition_scope"])
        bat_id = int(row["striker_id"])
        bat_name = str(row["striker_name_clean"])
        bowl_id = int(row["bowler_id"])
        bowl_name = str(row["bowler_name_clean"])
        balls = int(row["balls_faced"])
        runs = int(row["runs_scored"])
        fours = int(row["fours"])
        sixes = int(row["sixes"])
        outs = int(row["dismissals"])
        dots = int(row["dot_balls"])
        avg_p = round(float(row["avg_pressure_score"]), 2)

        sr = round((runs / balls * 100.0), 2) if balls > 0 else 0.0
        dot_pct = round((dots / balls * 100.0), 1) if balls > 0 else 0.0
        boundary_pct = round(((fours + sixes) / balls * 100.0), 1) if balls > 0 else 0.0
        avg = round((runs / outs), 2) if outs > 0 else None
        bpd = round((balls / outs), 1) if outs > 0 else None

        if balls < 6:
            tier = "Very Low Sample (<6 balls)"
        elif balls < 18:
            tier = "Low Sample (6-17 balls)"
        elif balls < 30:
            tier = "Moderate Sample (18-29 balls)"
        else:
            tier = "Robust Sample (>=30 balls)"

        tier_counts[tier] += 1
        is_reliable = (balls >= 18)
        is_ranked_involved = ((scope, bat_id) in ranked_batter_ids) or ((scope, bowl_id) in ranked_bowler_ids)

        matchup_id = f"{scope}_{bat_id}_{bowl_id}"
        matchup_key = f"{bat_name} vs {bowl_name} [{scope}]"

        record = {
            "matchup_id": matchup_id,
            "matchup_key": matchup_key,
            "competition_scope": scope,
            "batter_id": bat_id,
            "batter_name": bat_name,
            "bowler_id": bowl_id,
            "bowler_name": bowl_name,
            "balls_faced": balls,
            "runs_scored": runs,
            "dismissals": outs,
            "fours": fours,
            "sixes": sixes,
            "dot_balls": dots,
            "strike_rate": sr,
            "batting_average": avg,
            "balls_per_dismissal": bpd,
            "dot_percentage": dot_pct,
            "boundary_percentage": boundary_pct,
            "avg_pressure_score": avg_p,
            "sample_tier": tier,
            "is_statistically_reliable": is_reliable,
            "ranked_player_involved": is_ranked_involved
        }

        matchups_list.append(record)
        matchups_by_key[matchup_key] = record
        if is_ranked_involved:
            ranked_matchups.append(record)

    store_3 = {
        "metadata": {
            "store_name": "head_to_head_matrix",
            "version": "1.0.0",
            "description": "Exhaustive batter vs bowler head-to-head records across IPL and T20I with explicit sample limitation tiers.",
            "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_matchups": len(matchups_list),
            "ipl_matchups": sum(1 for m in matchups_list if m["competition_scope"] == "IPL"),
            "t20i_matchups": sum(1 for m in matchups_list if m["competition_scope"] == "T20I"),
            "matchups_with_ranked_players": len(ranked_matchups),
            "sample_tier_distribution": tier_counts,
            "sample_limitations_legend": {
                "Very Low Sample (<6 balls)": "Exploratory sample (<6 balls). Single-event volatility dominates signal. Do NOT draw tactical conclusions.",
                "Low Sample (6-17 balls)": "Early sample (6-17 balls). Useful for tactical orientation only; high confidence intervals.",
                "Moderate Sample (18-29 balls)": "Indicative sample (18-29 balls). Emerging tactical trend with moderate statistical power.",
                "Robust Sample (>=30 balls)": "Statistically reliable sample (>=30 balls). High statistical confidence for head-to-head match-up planning."
            }
        },
        "matchups": matchups_list,
        "by_key": matchups_by_key
    }

    out_file = DATA_OUT_DIR / "head_to_head_matrix.json"
    with open(out_file, "w") as f:
        json.dump(store_3, f, indent=2)

    sz_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"  Successfully wrote {len(matchups_list)} matchups ({len(ranked_matchups)} involving ranked players) to {out_file} ({sz_mb:.2f} MB) in {time.time()-t0:.2f}s")
    return store_3


def generate_data_dictionary():
    """
    Generate output/phase4/data/data_dictionary.md documenting all fields,
    formulas, and sample definitions across the three scouting stores.
    """
    dict_path = DATA_OUT_DIR / "data_dictionary.md"
    content = r"""# SupeRR Intelligence — Scouting Data Stores: Data Dictionary

**Version**: `1.0.0`  
**Parent Framework**: SupeRR Intelligence Phase 4.2 Scouting Store Builder  
**Methodology Freeze**: `CPRI-v1.0.0-PROD-FREEZE` (Phase 3.5)  
**Location**: `output/phase4/data/`  

---

## 1. Overview of Scouting Data Stores

Phase 4.2 constructs three compact, structured, queryable JSON data stores to power real-time AI scouting and analytics without reloading multi-gigabyte delivery files.

| File Name | Primary Purpose | Record Scope | Target Size |
|:---|:---|:---|:---:|
| [`player_scouting_profiles.json`](output/phase4/data/player_scouting_profiles.json) | Complete profile for each ranked player: CPRI scores, components, confidence tiers, exposure, baseline stats, and bootstrap uncertainty. | 60 Players (40 Official Top 10 + 20 Provisional Top 5) | ~0.2 MB |
| [`player_contextual_splits.json`](output/phase4/data/player_contextual_splits.json) | Situational breakdowns: Powerplay, Middle, Death, Pace vs Spin (Batters), vs RHB/LHB (Bowlers), and High vs Low Pressure contrasts. | 60 Players (40 Official Top 10 + 20 Provisional Top 5) | ~0.15 MB |
| [`head_to_head_matrix.json`](output/phase4/data/head_to_head_matrix.json) | Exhaustive batter vs bowler historical encounters in IPL and T20I with explicit sample size tiers and reliability indicators. | 25,985 Matchup Pairs (5,631 involving ranked players) | ~18 MB |

---

## 2. Store 1: `player_scouting_profiles.json`

### Field Definitions
- `profile_key` (string): Unique identifier formatted as `{competition_scope}_{role}_{player_id}`.
- `player_id` (integer): Official unique numeric player ID.
- `player_name` (string): Standardized player clean name.
- `competition_scope` (string): Tournament format: strictly `"IPL"` or `"T20I"`.
- `role` (string): Player specialization: strictly `"Batter"` or `"Bowler"`.
- `cohort` (string): Cohort designation: `"IPL Batters"`, `"T20I Batters"`, `"IPL Bowlers"`, or `"T20I Bowlers"`.
- `ranking_tier` (string): Official category: `"Official Top 10"` or `"Provisional Top 5"`.
- `official_rank` (integer): Rank within the designated cohort tier ($1$ to $10$ for Official, $1$ to $5$ for Provisional).
- `is_official_top10` (boolean): `true` if player achieved eligible Official Top 10 status.
- `is_provisional_top5` (boolean): `true` if player achieved Provisional Top 5 status (sub-threshold pressure sample).
- `is_champion` (boolean): `true` if player is the Rank 1 Official Champion in their cohort.
- `cpri_score` (float): Frozen Phase 3.5 composite CPRI score ($0.0$ to $100.0$).
- `components` (object):
  - `pressure_impact` (float): 40% weight.
  - `pressure_adaptability` (float): 25% weight.
  - `clutch_consistency` (float): 20% weight.
  - `reliability_confidence` (float): 15% weight.
- `confidence_tier` (string): `"High Confidence"` or `"Provisional"`.
- `status_reason` (string): Exact frozen rationale documenting qualification or provisional sample depth.
- `frozen_cpri_metrics` (object): Explicit container for authoritative Phase 3.5 frozen metrics:
  - `cpri_score`: Authoritative composite score.
  - `score_pressure_impact`, `score_adaptability`, `score_consistency`, `score_reliability`: Authoritative frozen component scores.
  - `frozen_pressure_deliveries`: 411 for Rinku Singh (match-state deliveries with pressure_score >= 50.0).
  - `frozen_total_deliveries`: Total delivery events.
  - `frozen_pressure_matches`: Matches with pressure.
- `exposure` (object):
  - `total_deliveries`: Total match-state deliveries in scope.
  - `pressure_deliveries`: Total deliveries under pressure ($\text{Pressure Score} \ge 50.0$). Authoritative Phase 3.5 count.
  - `pressure_matches`: Unique matches with pressure.
  - `sample_definition_notes`: Documentation distinguishing match-state pressure deliveries from striker balls faced.
  - `total_matches`: Total matches played.
  - `balls_per_match`: Average legal balls per match (specialist workload metric for bowlers).
  - `pressure_ratio`: $\text{pressure\_deliveries} / \text{total\_deliveries}$.
  - `pos_pressure_match_ratio`: Fraction of pressure matches with positive net performance residual.
  - `effective_pressure_sample_size`: Harmonic/cluster-discounted effective sample size ($n_{eff}$).
  - `pressure_specific_uncertainty`: Uncertainty score ($0.0$ to $100.0$).
- `performance_stats` (object):
  - **For Batters**: `balls_faced`, `actual_runs`, `strike_rate`, `batting_average`, `dismissals`, `fours`, `sixes`, `boundary_runs`, `boundary_percentage`, `dot_balls`, `dot_percentage`, and nested `pressure_stats` / `nonpressure_stats` (runs, balls, SR, average, WPA, run residual).
  - **For Bowlers**: `balls_bowled`, `overs_bowled`, `runs_conceded`, `credited_wickets`, `economy_rate`, `bowling_average`, `bowling_strike_rate`, `fours_conceded`, `sixes_conceded`, `boundary_percentage`, `dot_balls`, `dot_percentage`, and nested `pressure_stats` / `nonpressure_stats` (runs conceded, overs, wickets, economy, bowling average, WPA, run residual).
- `bootstrap_uncertainty` (object):
  - `is_audited` (boolean): `true` for Official Top 10 players audited under Phase 3.5 bootstrap simulation.
  - `primary_resampling_standard`: Resampling unit (Match-Level for IPL, Series-Level for T20I).
  - `prob_eligibility_pct`: Probability of meeting sample size thresholds across resampled replicates.
  - `prob_rank_1_pct`: Frequency of achieving Rank 1.
  - `prob_top10_pct`: Frequency of inclusion in Top 10.
  - `conditional_rank_median`: Median rank across eligible bootstrap replicates.
  - `conditional_rank_95_interval`: 95% empirical bootstrap rank interval `"[lower, upper]"`.
  - `conditional_cpri_mean`: Mean CPRI score across eligible bootstrap replicates.
  - `conditional_cpri_std_dev`: Statistical standard deviation of CPRI across replicates.
  - `conditional_cpri_95_ci`: 95% empirical bootstrap CPRI confidence interval.
  - `mc_standard_error_rank1_pct`: Monte Carlo standard error for Rank 1 probability ($SE_{MC} = \sqrt{p(1-p)/B}$).
  - `mc_standard_error_top10_pct`: Monte Carlo standard error for Top 10 probability.

---

## 3. Store 2: `player_contextual_splits.json`

### Field Definitions
- `innings_phase_splits` (object):
  - `powerplay`: Overs 1 to 6 (Deliveries with field restriction rules active).
  - `middle`: Overs 7 to 16 (Middle innings strike rotation and spin handling).
  - `death`: Overs 17 to 20 (High-leverage terminal overs).
- `bowling_type_splits` (Batters only):
  - `pace`: Performance against Pace / Seam bowlers.
  - `spin`: Performance against Spin bowlers (Off-spin, Leg-spin, SLA).
- `batter_hand_splits` (Bowlers only):
  - `rhb`: Performance against Right-Hand Batters.
  - `lhb`: Performance against Left-Hand Batters.
- `pressure_contrast` (object):
  - `high_pressure`: Deliveries where $\text{Pressure Score} \ge 50.0$.
  - `low_pressure`: Deliveries where $\text{Pressure Score} < 50.0$.
  - `delta_strike_rate` (Batters): $SR_{high} - SR_{low}$. Positive indicates acceleration under pressure.
  - `delta_economy` (Bowlers): $Econ_{high} - Econ_{low}$. Negative indicates improved run restriction under pressure.
  - `tactical_classification`:
    - Batters: `"Clutch Accelerant"` ($\Delta SR \ge +5.0$), `"Pressure Degrader"` ($\Delta SR \le -5.0$), or `"Anchor Stabilizer"` ($|\Delta SR| < 5.0$).
    - Bowlers: `"High-Leverage Constrictor"` ($\Delta Econ \le -0.50$), `"Pressure Vulnerable"` ($\Delta Econ \ge +0.50$), or `"Steady Executor"` ($|\Delta Econ| < 0.50$).

---

## 4. Store 3: `head_to_head_matrix.json`

### Sample Limitation Tiers
Every head-to-head record includes an explicit `sample_tier` to prevent LLMs from hallucinating certainty on low-sample encounters:
1. **`Very Low Sample (<6 balls)`**: Exploratory sample ($< 6$ balls). Variance completely dominates statistical signal. Tactical conclusions prohibited.
2. **`Low Sample (6-17 balls)`**: Early sample ($6\text{--}17$ balls). Indicates early tendencies; wide uncertainty intervals.
3. **`Moderate Sample (18-29 balls)`**: Indicative sample ($18\text{--}29$ balls). Emerging tactical trend with meaningful historical weight.
4. **`Robust Sample (>=30 balls)`**: Statistically reliable sample ($\ge 30$ balls). High statistical confidence for tactical planning.

### Metrics Computed
- `balls_faced`: Legal balls faced by the batter from this specific bowler.
- `runs_scored`: Total runs scored off the bat against this bowler.
- `dismissals`: Credited dismissals where bowler took batter's wicket (`bowler_wicket == 1`).
- `fours` & `sixes`: Boundaries hit by batter off bowler.
- `dot_balls`: Deliveries with zero runs scored off the bat.
- `strike_rate`: $(Runs / Balls) \times 100$.
- `batting_average`: $Runs / Dismissals$ (or `null` if $0$ dismissals).
- `balls_per_dismissal`: $Balls / Dismissals$ (or `null` if $0$ dismissals).
- `dot_percentage`: $(DotBalls / Balls) \times 100$.
- `boundary_percentage`: $((Fours + Sixes) / Balls) \times 100$.
- `avg_pressure_score`: Average game pressure score during this matchup.
- `is_statistically_reliable`: `true` if $\text{balls\_faced} \ge 18$.
- `ranked_player_involved`: `true` if batter or bowler belongs to the 60 official/provisional ranked players.
"""
    with open(dict_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[Step 5] Generated data dictionary at {dict_path}")


def main():
    print("=" * 75)
    print("STARTING SUPERR INTELLIGENCE - PHASE 4.2: SCOUTING STORE BUILDER")
    print("=" * 75)

    off_csv, off_json, unc_df, bat_p33, bowl_p33, deliv_df = load_upstream_data()

    store_1 = build_player_scouting_profiles(off_csv, unc_df, bat_p33, bowl_p33, deliv_df)
    store_2 = build_player_contextual_splits(off_csv, bat_p33, bowl_p33, deliv_df)
    store_3 = build_head_to_head_matrix(off_csv, deliv_df)

    generate_data_dictionary()

    print("\n" + "=" * 75)
    print("PHASE 4.2 DATA STORE GENERATION COMPLETE")
    print(f"Store 1 Profiles: {len(store_1['profiles'])} records")
    print(f"Store 2 Splits:   {len(store_2['splits'])} records")
    print(f"Store 3 Matchups: {len(store_3['matchups'])} records")
    print("=" * 75)


if __name__ == "__main__":
    main()
