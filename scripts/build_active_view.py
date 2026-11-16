#!/usr/bin/env python3
"""
scripts/build_active_view.py
============================
Builds the supplementary 'Recently active in data' (last 12 months) rankings
for batters and bowlers from the supplied match dataset and frozen Phase 8 deliverables.

Rules:
- Governed strictly by docs/methodology/v5/ELIGIBILITY_RULE.md.
- T_max is derived from data (2026-11-01), never typed.
- Evaluates only in-scope IPL and senior men's T20I matches.
- Ranks strictly by RAW CPRI (no formula modifications or adjustments).
- Outputs:
  * output/phase12_active/active_top10_batters.csv
  * output/phase12_active/active_top10_bowlers.csv
  * output/phase12_active/active_top25_batters.csv
  * output/phase12_active/active_top25_bowlers.csv
  * output/phase12_active/active_sensitivity_table.csv
  * output/phase12_active/active_summary.json
"""
import argparse
import json
import sys
from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.ppr_engine import DEFAULT_EVIDENCE_CONFIG

PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
PROCESSED_DIR = REPO_ROOT / "output" / "processed"
OUT_DIR = REPO_ROOT / "output" / "phase12_active"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Build supplementary active-only rankings from match data.")
    parser.add_argument(
        "--raw-zip",
        type=str,
        default=None,
        help="Optional path to raw SupeRR_Intelligence_Phase1.zip"
    )
    return parser.parse_args()


def load_deliveries(raw_zip_path: str = None) -> pd.DataFrame:
    """Load deliveries with match dates and in-scope flag."""
    if raw_zip_path and Path(raw_zip_path).exists():
        print(f"Reading deliveries from zip archive: {raw_zip_path}")
        with zipfile.ZipFile(raw_zip_path, 'r') as z:
            with z.open("deliveries_enriched.csv") as f:
                return pd.read_csv(f, usecols=['striker_id', 'bowler_id', 'match_date', 'in_scope_competition'])
    
    deliv_csv = PROCESSED_DIR / "deliveries_enriched.csv"
    if deliv_csv.exists():
        print(f"Reading deliveries from pipeline processed file: {deliv_csv}")
        return pd.read_csv(deliv_csv, usecols=['striker_id', 'bowler_id', 'match_date', 'in_scope_competition'])

    # Fallback to Desktop zip if available
    desktop_zip = REPO_ROOT.parent.parent / "SupeRR_Intelligence_Phase1.zip"
    if desktop_zip.exists():
        print(f"Reading deliveries from workspace root zip: {desktop_zip}")
        with zipfile.ZipFile(desktop_zip, 'r') as z:
            with z.open("deliveries_enriched.csv") as f:
                return pd.read_csv(f, usecols=['striker_id', 'bowler_id', 'match_date', 'in_scope_competition'])

    raise FileNotFoundError("Could not find deliveries_enriched.csv in output/processed/ or zip archive.")


def main():
    args = parse_args()
    print("======================================================================")
    print("SUPERR SELECTOR: RECENT MATCH ACTIVITY PIPELINE (PHASE 12 ACTIVE)")
    print("======================================================================")

    # 1. Load frozen Phase 8 deliverables
    print("[1/5] Loading frozen Phase 8 reference datasets...")
    p8_bat_pop = pd.read_csv(PHASE8_DIR / "batter_full_population.csv")
    p8_bowl_pop = pd.read_csv(PHASE8_DIR / "bowler_full_population.csv")
    p8_bat_top10 = pd.read_csv(PHASE8_DIR / "official_top10_batters.csv")
    p8_bowl_top10 = pd.read_csv(PHASE8_DIR / "official_top10_bowlers.csv")
    b_uncert = pd.read_csv(PHASE8_DIR / "batter_rank_uncertainty.csv").set_index("player_id")
    bw_uncert = pd.read_csv(PHASE8_DIR / "bowler_rank_uncertainty.csv").set_index("player_id")

    # 2. Load deliveries & compute last_played
    print("[2/5] Parsing match deliveries and computing last played dates per role...")
    deliv = load_deliveries(args.raw_zip)
    deliv_in = deliv[deliv['in_scope_competition'] == True].copy()
    deliv_in['date'] = pd.to_datetime(deliv_in['match_date']).dt.tz_localize(None)

    max_date = deliv_in['date'].max()
    print(f"  Maximum in-scope match date in dataset (T_max): {max_date.strftime('%Y-%m-%d')}")

    last_bat_series = deliv_in.groupby('striker_id')['date'].max()
    last_bowl_series = deliv_in.groupby('bowler_id')['date'].max()

    last_bat_dict = last_bat_series.to_dict()
    last_bowl_dict = last_bowl_series.to_dict()

    # 3. Build Active Batters and Bowlers (12-month primary window)
    print("[3/5] Applying 12-month activity window (matches >= T_max - 12 months)...")
    cutoff_12m = max_date - pd.DateOffset(months=12)
    cutoff_12m_str = cutoff_12m.strftime('%Y-%m-%d')
    print(f"  12-month activity threshold date: {cutoff_12m_str}")

    # Official Eligible pool
    el_bat = p8_bat_pop[p8_bat_pop['eligibility_tier'] == 'Official Eligible'].copy()
    el_bowl = p8_bowl_pop[p8_bowl_pop['eligibility_tier'] == 'Official Eligible'].copy()

    el_bat['last_played_dt'] = el_bat['player_id'].map(last_bat_dict)
    el_bowl['last_played_dt'] = el_bowl['player_id'].map(last_bowl_dict)

    el_bat['last_played'] = el_bat['last_played_dt'].dt.strftime('%Y-%m-%d')
    el_bowl['last_played'] = el_bowl['last_played_dt'].dt.strftime('%Y-%m-%d')

    el_bat['is_active_12m'] = el_bat['last_played_dt'] >= cutoff_12m
    el_bowl['is_active_12m'] = el_bowl['last_played_dt'] >= cutoff_12m

    act_bat_all = el_bat[el_bat['is_active_12m']].sort_values(by='cpri_score', ascending=False).reset_index(drop=True)
    act_bowl_all = el_bowl[el_bowl['is_active_12m']].sort_values(by='cpri_score', ascending=False).reset_index(drop=True)

    def format_active_df(df, uncert_map, role_name):
        records = []
        for idx, r in df.iterrows():
            pid = int(r['player_id'])
            off_rank = int(r['official_rank']) if pd.notnull(r['official_rank']) else None
            in_top10 = bool(off_rank is not None and off_rank <= 10)
            p_balls = int(r['pressure_deliveries'])
            tier = DEFAULT_EVIDENCE_CONFIG.classify(p_balls)

            # Retrieve full-population bootstrap uncertainty
            u_info = uncert_map.loc[pid] if pid in uncert_map.index else None
            p5 = int(u_info['rank_p5']) if u_info is not None else None
            p95 = int(u_info['rank_p95']) if u_info is not None else None
            ci_disp = f"[{p5}, {p95}]" if p5 is not None and p95 is not None else "—"

            records.append({
                'rank': idx + 1,
                'player_id': pid,
                'player_name': str(r['player_name']),
                'cpri_score': round(float(r['cpri_score']), 2),
                'pressure_deliveries': p_balls,
                'last_played': str(r['last_played']),
                'evidence_tier': tier,
                'official_rank': off_rank,
                'in_official_top10': in_top10,
                'rank_p5': p5,
                'rank_p95': p95,
                'rank_ci_90': ci_disp,
                'rank_uncertainty_source': "from full-population bootstrap, not recomputed for the active view"
            })
        return pd.DataFrame(records)

    act_bat_formatted = format_active_df(act_bat_all, b_uncert, "Batter")
    act_bowl_formatted = format_active_df(act_bowl_all, bw_uncert, "Bowler")

    # Save Top 10 and Top 25
    top10_bat = act_bat_formatted.head(10)
    top25_bat = act_bat_formatted.head(25)
    top10_bowl = act_bowl_formatted.head(10)
    top25_bowl = act_bowl_formatted.head(25)

    top10_bat.to_csv(OUT_DIR / "active_top10_batters.csv", index=False)
    top25_bat.to_csv(OUT_DIR / "active_top25_batters.csv", index=False)
    top10_bowl.to_csv(OUT_DIR / "active_top10_bowlers.csv", index=False)
    top25_bowl.to_csv(OUT_DIR / "active_top25_bowlers.csv", index=False)

    print(f"  Saved active Top 10 Batters -> {OUT_DIR / 'active_top10_batters.csv'}")
    print(f"  Saved active Top 10 Bowlers -> {OUT_DIR / 'active_top10_bowlers.csv'}")
    print(f"  Saved active Top 25 Batters -> {OUT_DIR / 'active_top25_batters.csv'}")
    print(f"  Saved active Top 25 Bowlers -> {OUT_DIR / 'active_top25_bowlers.csv'}")

    # 4. Generate Sensitivity Analysis (6, 12, 18 Months)
    print("[4/5] Generating sensitivity analysis across 6, 12, and 18-month windows...")
    sensitivity_records = []
    windows = [
        ("6 Months", 6),
        ("12 Months (Primary)", 12),
        ("18 Months", 18),
    ]

    for w_label, months in windows:
        w_cutoff = max_date - pd.DateOffset(months=months)
        w_cutoff_str = w_cutoff.strftime('%Y-%m-%d')

        # Batters
        b_act = el_bat[el_bat['last_played_dt'] >= w_cutoff].sort_values(by='cpri_score', ascending=False).reset_index(drop=True)
        b_top10_ids = set(b_act.head(10)['player_id'])
        p8_b_ids = set(p8_bat_top10['player_id'])

        b_dropped = [r['player_name'] for _, r in p8_bat_top10.iterrows() if r['player_id'] not in b_top10_ids]
        b_entered = [r['player_name'] for _, r in b_act.head(10).iterrows() if r['player_id'] not in p8_b_ids]

        # Bowlers
        bw_act = el_bowl[el_bowl['last_played_dt'] >= w_cutoff].sort_values(by='cpri_score', ascending=False).reset_index(drop=True)
        bw_top10_ids = set(bw_act.head(10)['player_id'])
        p8_bw_ids = set(p8_bowl_top10['player_id'])

        bw_dropped = [r['player_name'] for _, r in p8_bowl_top10.iterrows() if r['player_id'] not in bw_top10_ids]
        bw_entered = [r['player_name'] for _, r in bw_act.head(10).iterrows() if r['player_id'] not in p8_bw_ids]

        sensitivity_records.append({
            'window_label': w_label,
            'window_months': months,
            'cutoff_date': w_cutoff_str,
            'batters_qualifying_count': len(b_act),
            'batters_dropped_from_top10': "; ".join(b_dropped) if b_dropped else "None",
            'batters_entered_top10': "; ".join(b_entered) if b_entered else "None",
            'bowlers_qualifying_count': len(bw_act),
            'bowlers_dropped_from_top10': "; ".join(bw_dropped) if bw_dropped else "None",
            'bowlers_entered_top10': "; ".join(bw_entered) if bw_entered else "None",
        })

    sens_df = pd.DataFrame(sensitivity_records)
    sens_df.to_csv(OUT_DIR / "active_sensitivity_table.csv", index=False)
    print(f"  Saved sensitivity analysis -> {OUT_DIR / 'active_sensitivity_table.csv'}")

    # 5. Build Summary JSON
    print("[5/5] Compiling active summary JSON payload...")
    summary = {
        "metadata": {
            "title": "SupeRR Selector Supplementary Active View",
            "rule_reference": "docs/methodology/v5/ELIGIBILITY_RULE.md",
            "rule_type": "Post-hoc uniform match activity filter",
            "last_match_date": max_date.strftime('%Y-%m-%d'),
            "primary_window_months": 12,
            "primary_cutoff_date": cutoff_12m_str,
            "competitions_scope": "IPL and senior men's T20Is",
            "qualifying_active_batters_count": len(act_bat_all),
            "qualifying_active_bowlers_count": len(act_bowl_all),
            "bootstrap_rank_uncertainty_note": "from full-population bootstrap, not recomputed for the active view"
        },
        "active_top10_batters": top10_bat.to_dict(orient="records"),
        "active_top10_bowlers": top10_bowl.to_dict(orient="records"),
        "sensitivity_analysis": sensitivity_records
    }

    with open(OUT_DIR / "active_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved summary JSON -> {OUT_DIR / 'active_summary.json'}")

    print("\n======================================================================")
    print("ACTIVE VIEW GENERATION COMPLETE")
    print("======================================================================")


if __name__ == "__main__":
    main()
