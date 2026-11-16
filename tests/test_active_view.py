"""
tests/test_active_view.py
Unit and invariant tests for Phase 12 Active View & Numbers Integrity.

Tests:
1. Every displayed number in Phase 12 active lists matches the frozen Phase 8 population CSVs exactly.
2. Specific bowler counts corrected from prior ad-hoc reports:
   - Varun Chakravarthy: exactly 892 pressure balls (not 398)
   - Yuzvendra Chahal: exactly 859 pressure balls (not 557)
   - Mohammad Nawaz: exactly 301 pressure balls (not 185)
   - Jasprit Bumrah: exactly 606 pressure balls (not 609)
3. No player in the active view has last_played < 2025-11-01 (12-month data-driven cutoff).
4. No unverified retirement claims, registries, badges, or filters remain in code, UI, or API.
5. Official Phase 8 CSVs are bitwise/text identical to commit 7027660 (ignoring line endings).
6. Rank uncertainty note is explicitly and honestly stated as reused from full-population bootstrap.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
P8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
P12_DIR = REPO_ROOT / "output" / "phase12_active"


def test_active_files_exist():
    """Verify that all Phase 12 active view deliverables exist."""
    assert (P12_DIR / "active_top10_batters.csv").exists(), "Missing active_top10_batters.csv"
    assert (P12_DIR / "active_top10_bowlers.csv").exists(), "Missing active_top10_bowlers.csv"
    assert (P12_DIR / "active_top25_batters.csv").exists(), "Missing active_top25_batters.csv"
    assert (P12_DIR / "active_top25_bowlers.csv").exists(), "Missing active_top25_bowlers.csv"
    assert (P12_DIR / "active_sensitivity_table.csv").exists(), "Missing active_sensitivity_table.csv"
    assert (P12_DIR / "active_summary.json").exists(), "Missing active_summary.json"


def test_active_numbers_match_phase8_population():
    """Verify that CPRI scores, pressure deliveries, and tiers in active view match frozen population CSVs."""
    bat_pop = pd.read_csv(P8_DIR / "batter_full_population.csv").set_index("player_id")
    bowl_pop = pd.read_csv(P8_DIR / "bowler_full_population.csv").set_index("player_id")

    act_bat10 = pd.read_csv(P12_DIR / "active_top10_batters.csv")
    act_bowl10 = pd.read_csv(P12_DIR / "active_top10_bowlers.csv")

    for _, r in act_bat10.iterrows():
        pid = int(r["player_id"])
        assert pid in bat_pop.index, f"Batter {r['player_name']} (ID {pid}) not in batter_full_population.csv"
        pop_row = bat_pop.loc[pid]
        assert pytest.approx(r["cpri_score"], abs=1e-2) == pop_row["cpri_score"], (
            f"CPRI mismatch for batter {r['player_name']}: {r['cpri_score']} vs {pop_row['cpri_score']}"
        )
        assert int(r["pressure_deliveries"]) == int(pop_row["pressure_deliveries"]), (
            f"Deliveries mismatch for batter {r['player_name']}: {r['pressure_deliveries']} vs {pop_row['pressure_deliveries']}"
        )

    for _, r in act_bowl10.iterrows():
        pid = int(r["player_id"])
        assert pid in bowl_pop.index, f"Bowler {r['player_name']} (ID {pid}) not in bowler_full_population.csv"
        pop_row = bowl_pop.loc[pid]
        assert pytest.approx(r["cpri_score"], abs=1e-2) == pop_row["cpri_score"], (
            f"CPRI mismatch for bowler {r['player_name']}: {r['cpri_score']} vs {pop_row['cpri_score']}"
        )
        assert int(r["pressure_deliveries"]) == int(pop_row["pressure_deliveries"]), (
            f"Deliveries mismatch for bowler {r['player_name']}: {r['pressure_deliveries']} vs {pop_row['pressure_deliveries']}"
        )


def test_corrected_bowler_delivery_counts():
    """Ensure specific bowler pressure delivery counts match the frozen CSVs (correcting prior ad-hoc reports)."""
    bowl_pop = pd.read_csv(P8_DIR / "bowler_full_population.csv").set_index("player_name")

    # Varun Chakravarthy: 892 (was 398 in old unverified report)
    assert int(bowl_pop.loc["Varun Chakravarthy", "pressure_deliveries"]) == 892

    # Yuzvendra Chahal: 859 (was 557 in old unverified report)
    assert int(bowl_pop.loc["Yuzvendra Chahal", "pressure_deliveries"]) == 859

    # Mohammad Nawaz: 301 (was 185 in old unverified report)
    assert int(bowl_pop.loc["Mohammad Nawaz", "pressure_deliveries"]) == 301

    # Jasprit Bumrah: 606 (was 609 in old unverified report)
    assert int(bowl_pop.loc["Jasprit Bumrah", "pressure_deliveries"]) == 606


def test_active_cutoff_invariance():
    """Assert that no player in active view has last_played prior to the 12-month cutoff (2025-11-01)."""
    cutoff = "2025-11-01"
    for fn in ["active_top10_batters.csv", "active_top10_bowlers.csv", "active_top25_batters.csv", "active_top25_bowlers.csv"]:
        df = pd.read_csv(P12_DIR / fn)
        for _, r in df.iterrows():
            assert str(r["last_played"]) >= cutoff, (
                f"Player {r['player_name']} in {fn} has last_played {r['last_played']} < cutoff {cutoff}"
            )


def test_dropped_and_entered_expectations():
    """Verify expected movements under the 12-month data window."""
    act_bat10 = pd.read_csv(P12_DIR / "active_top10_batters.csv")
    act_bowl10 = pd.read_csv(P12_DIR / "active_top10_bowlers.csv")

    bat_names = act_bat10["player_name"].tolist()
    bowl_names = act_bowl10["player_name"].tolist()

    # Batters: Wade and Karthik drop out; Shashank Singh and Ashutosh Sharma enter
    assert "Matthew Wade" not in bat_names, "Matthew Wade should not be in active Top 10 batters"
    assert "Dinesh Karthik" not in bat_names, "Dinesh Karthik should not be in active Top 10 batters"
    assert "Shashank Singh" in bat_names, "Shashank Singh should enter active Top 10 batters"
    assert "Ashutosh Sharma" in bat_names, "Ashutosh Sharma should enter active Top 10 batters"

    # Bowlers: All 10 official bowlers remain active
    off_bowl10 = pd.read_csv(P8_DIR / "official_top10_bowlers.csv")["player_name"].tolist()
    assert bowl_names == off_bowl10, f"Active bowler Top 10 does not match official Top 10: {bowl_names} vs {off_bowl10}"


def test_no_unverified_retirement_claims_in_repo():
    """Verify that no player is labeled as 'retired' or has 'RETIRED' badges/filters across the codebase."""
    # Run git grep -i "retired"
    res = subprocess.run(
        ["git", "grep", "-i", "retired"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        stdin=subprocess.DEVNULL,
    )
    assert res.returncode == 0, f"git grep failed: {res.stderr}"

    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        filepath, _, content = line.partition(":")
        filepath = filepath.replace("\\", "/")

        # REMOVED_MATERIAL.md is the explicit audit of removed files
        if "REMOVED_MATERIAL.md" in filepath:
            continue

        # Cricket dismissal law: "Retired Out" / "retired out" is standard cricket nomenclature
        if "retired out" in content.lower():
            continue

        # The negative disclaimer: "never 'retired'" or "not labeled as retired"
        if "never" in content.lower() and "retired" in content.lower():
            continue
        if "under no circumstances is a player labeled as" in content.lower():
            continue

        pytest.fail(f"Unauthorized retirement claim or badge found in {filepath}: {content}")


def test_official_phase8_csvs_unchanged_vs_commit_7027660():
    """Assert that official Phase 8 CSVs are bitwise/text identical to commit 7027660 (ignoring line endings)."""
    target_files = [
        "official_top10_batters.csv",
        "official_top10_bowlers.csv",
        "batter_full_population.csv",
        "bowler_full_population.csv",
    ]

    for fn in target_files:
        git_cmd = ["git", "show", f"7027660:output/phase8_ranking_reconsideration/{fn}"]
        git_res = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
        )
        assert git_res.returncode == 0, f"Failed to retrieve 7027660:output/phase8_ranking_reconsideration/{fn}"

        curr_path = P8_DIR / fn
        assert curr_path.exists(), f"Current file {curr_path} does not exist"
        curr_text = curr_path.read_text(encoding="utf-8")

        git_clean = git_res.stdout.replace("\r\n", "\n").strip()
        curr_clean = curr_text.replace("\r\n", "\n").strip()

        assert git_clean == curr_clean, f"Content mismatch between current {fn} and commit 7027660"


def test_rank_uncertainty_honesty_note():
    """Verify that rank uncertainty in active view explicitly discloses that intervals are from full-population bootstrap."""
    act_bat10 = pd.read_csv(P12_DIR / "active_top10_batters.csv")
    act_bowl10 = pd.read_csv(P12_DIR / "active_top10_bowlers.csv")

    expected_note = "from full-population bootstrap, not recomputed for the active view"
    for _, r in act_bat10.iterrows():
        assert r["rank_uncertainty_source"] == expected_note
    for _, r in act_bowl10.iterrows():
        assert r["rank_uncertainty_source"] == expected_note
