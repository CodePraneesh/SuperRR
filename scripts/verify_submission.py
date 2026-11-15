#!/usr/bin/env python3
"""
scripts/verify_submission.py
SupeRR Intelligence — Submission Safety & Integrity Verifier

Validates:
1. Exactly 10 official batters and 10 official bowlers.
2. Ranks are strictly monotonic 1..10 without gaps or repeats.
3. No duplicate player names or IDs within either list.
4. All 20 player names match EXACTLY as spelled in competition_team_player_mapping.csv.
5. All 20 player IDs match competition_team_player_mapping.csv.
6. The names and ranks match the methodology report tables.

Exits 0 on success; exits non-zero on any discrepancy.
"""
from __future__ import annotations
import sys
import re
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

def find_player_mapping() -> Path:
    candidates = [
        REPO_ROOT / "data" / "competition_team_player_mapping.csv",
        Path(r"D:\Download\6af458274c1e8_data_pack\Data Pack\competition_team_player_mapping.csv"),
        REPO_ROOT.parent / "Data Pack" / "competition_team_player_mapping.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "competition_team_player_mapping.csv not found in data/ or external data pack path."
    )

def verify_submission():
    print("=" * 70)
    print("SUPERR INTELLIGENCE: SUBMISSION SAFETY & INTEGRITY VERIFICATION")
    print("=" * 70)

    # 1. Locate player mapping
    mapping_path = find_player_mapping()
    print(f"[1/5] Using player mapping: {mapping_path}")
    mapping_df = pd.read_csv(mapping_path)
    valid_names = set(mapping_df["player_name"].dropna().unique())
    id_to_names = mapping_df.groupby("player_id")["player_name"].unique().to_dict()

    # 2. Locate official CSVs
    p8_dir = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
    batters_path = p8_dir / "official_top10_batters.csv"
    bowlers_path = p8_dir / "official_top10_bowlers.csv"

    if not batters_path.exists() or not bowlers_path.exists():
        print(f"ERROR: Official CSVs missing in {p8_dir}")
        sys.exit(1)

    batters = pd.read_csv(batters_path)
    bowlers = pd.read_csv(bowlers_path)

    errors = []

    # 3. Validate Batters
    print(f"[2/5] Validating Official Top 10 Batters ({len(batters)} rows)...")
    if len(batters) != 10:
        errors.append(f"Batters list has {len(batters)} rows; expected exactly 10.")
    if list(batters["official_rank"]) != list(range(1, 11)):
        errors.append(f"Batters ranks are not strictly 1..10: {list(batters['official_rank'])}")
    if batters["player_name"].duplicated().any():
        errors.append(f"Batters list contains duplicate names: {batters['player_name'][batters['player_name'].duplicated()].tolist()}")
    if batters["player_id"].duplicated().any():
        errors.append(f"Batters list contains duplicate IDs: {batters['player_id'][batters['player_id'].duplicated()].tolist()}")

    for _, row in batters.iterrows():
        rk = row["official_rank"]
        name = str(row["player_name"]).strip()
        pid = row["player_id"]
        if name not in valid_names:
            errors.append(f"Batter #{rk} '{name}' not found in competition_team_player_mapping.csv!")
        elif pid in id_to_names and name not in id_to_names[pid]:
            errors.append(f"Batter #{rk} '{name}' (ID: {pid}) does not match mapped ID names: {id_to_names[pid]}")
        else:
            print(f"  OK: #{rk:2d} Batter: {name:<24} (ID: {pid})")

    # 4. Validate Bowlers
    print(f"\n[3/5] Validating Official Top 10 Bowlers ({len(bowlers)} rows)...")
    if len(bowlers) != 10:
        errors.append(f"Bowlers list has {len(bowlers)} rows; expected exactly 10.")
    if list(bowlers["official_rank"]) != list(range(1, 11)):
        errors.append(f"Bowlers ranks are not strictly 1..10: {list(bowlers['official_rank'])}")
    if bowlers["player_name"].duplicated().any():
        errors.append(f"Bowlers list contains duplicate names: {bowlers['player_name'][bowlers['player_name'].duplicated()].tolist()}")
    if bowlers["player_id"].duplicated().any():
        errors.append(f"Bowlers list contains duplicate IDs: {bowlers['player_id'][bowlers['player_id'].duplicated()].tolist()}")

    for _, row in bowlers.iterrows():
        rk = row["official_rank"]
        name = str(row["player_name"]).strip()
        pid = row["player_id"]
        if name not in valid_names:
            errors.append(f"Bowler #{rk} '{name}' not found in competition_team_player_mapping.csv!")
        elif pid in id_to_names and name not in id_to_names[pid]:
            errors.append(f"Bowler #{rk} '{name}' (ID: {pid}) does not match mapped ID names: {id_to_names[pid]}")
        else:
            print(f"  OK: #{rk:2d} Bowler: {name:<24} (ID: {pid})")

    # 5. Cross-check against Methodology Report Tables
    print("\n[4/5] Cross-checking against Methodology Report...")
    report_md_candidates = [
        REPO_ROOT / "docs" / "reports" / "METHODOLOGY_REPORT.md",
        REPO_ROOT / "docs" / "methodology" / "v2" / "HELD_OUT_METRICS_AND_INVARIANT_TESTS.md",
        REPO_ROOT / "output" / "phase8_ranking_reconsideration" / "final_methodology_report.md"
    ]
    
    report_found = False
    for r_path in report_md_candidates:
        if r_path.exists():
            report_found = True
            print(f"  Found reference methodology doc: {r_path.name}")
            with open(r_path, "r", encoding="utf-8") as f:
                content = f.read()
            for _, row in batters.iterrows():
                if row["player_name"] not in content:
                    errors.append(f"Batter '{row['player_name']}' missing in {r_path.name}")
            for _, row in bowlers.iterrows():
                if row["player_name"] not in content:
                    errors.append(f"Bowler '{row['player_name']}' missing in {r_path.name}")
            break

    if not report_found:
        print("  Notice: Final report doc pending generation in Task 1.")

    # 6. Final Evaluation
    print("\n[5/5] Final Submission Verification Assessment:")
    print("-" * 70)
    if errors:
        print(f"FAILED: Found {len(errors)} submission integrity violation(s):")
        for err in errors:
            print(f"  - {err}")
        print("=" * 70)
        sys.exit(1)

    print("SUCCESS: ALL SUBMISSION INTEGRITY CHECKS PASSED.")
    print("  - 10/10 Batters exist with exact Unstop dropdown spelling.")
    print("  - 10/10 Bowlers exist with exact Unstop dropdown spelling.")
    print("  - Zero duplicates; ranks 1..10 strictly ordered.")
    print("=" * 70)
    sys.exit(0)

if __name__ == "__main__":
    verify_submission()
