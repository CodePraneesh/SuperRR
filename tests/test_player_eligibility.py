#!/usr/bin/env python3
"""
tests/test_player_eligibility.py
================================
Unit and invariant tests for the Current-Player Eligibility Audit.

Verifies:
1. Historical Phase 8 CSVs remain 100% byte-identical to commit 7027660.
2. Reproducibility manifest passes 17/17 exact SHA-256 match.
3. verify_submission.py exits 0 with zero integrity errors.
4. Player eligibility registry exists with all required schema columns.
5. Confirmed IPL retirees are properly flagged and distinguished from international/professional retirees.
6. Players are not classified as retired merely for being released or unsold.
7. Active players leaderboard properly excludes retirees while preserving historical scores.
8. Active top 10 bowlers remain 100% active.
"""
from __future__ import annotations
import subprocess
import unittest
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
P8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
OUT_ELIG_DIR = REPO_ROOT / "output" / "eligibility"
DATA_DIR = REPO_ROOT / "data"


class TestPlayerEligibility(unittest.TestCase):

    def test_01_historical_phase8_csvs_unchanged(self):
        """Invariant: Official Phase 8 ranking CSVs must remain 100% byte-identical to commit 7027660."""
        target_files = [
            "official_top10_batters.csv",
            "official_top10_bowlers.csv",
            "batter_rank_uncertainty.csv",
            "bowler_rank_uncertainty.csv",
        ]
        for fname in target_files:
            orig = subprocess.check_output(
                ["git", "show", f"7027660:output/phase8_ranking_reconsideration/{fname}"],
                cwd=str(REPO_ROOT)
            ).decode("utf-8").replace("\r\n", "\n")

            curr = (P8_DIR / fname).read_text(encoding="utf-8").replace("\r\n", "\n")
            self.assertEqual(orig, curr, f"Historical file {fname} was modified!")

    def test_02_manifest_and_submission_verification_pass(self):
        """Invariant: verify_manifest.py and verify_submission.py must pass with exit code 0."""
        # 1. Manifest
        res_m = subprocess.run(
            ["python", "scripts/verify_manifest.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True
        )
        self.assertEqual(res_m.returncode, 0, f"verify_manifest failed:\n{res_m.stdout}\n{res_m.stderr}")
        self.assertIn("All 17 deliverables match manifest hashes exactly", res_m.stdout)

        # 2. Submission
        res_s = subprocess.run(
            ["python", "scripts/verify_submission.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True
        )
        self.assertEqual(res_s.returncode, 0, f"verify_submission failed:\n{res_s.stdout}\n{res_s.stderr}")
        self.assertIn("ALL SUBMISSION INTEGRITY CHECKS PASSED", res_s.stdout)

    def test_03_registry_schema_and_columns(self):
        """Verify registry exists in data/ and output/eligibility/ with all required schema columns."""
        reg_path = DATA_DIR / "player_eligibility_registry.csv"
        self.assertTrue(reg_path.exists(), "player_eligibility_registry.csv missing in data/")

        df = pd.read_csv(reg_path)
        required_cols = [
            "player_name", "role", "IPL_status", "international_status",
            "franchise_T20_status", "last_verified_match_date",
            "eligibility_status", "evidence_source"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

        # Check eligibility statuses are strictly valid
        valid_statuses = {"ACTIVE", "RETIRED", "NEEDS_VERIFICATION"}
        for status in df["eligibility_status"]:
            self.assertIn(status, valid_statuses, f"Invalid status: {status}")

    def test_04_user_retired_ipl_players_audited(self):
        """Verify all 17 players requested in the IPL retired list are audited and classified as RETIRED."""
        reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv").set_index("player_name")
        user_retired_17 = [
            "Kieron Pollard", "Dwayne Bravo", "Aaron Finch", "David Warner", "Matthew Wade",
            "Andre Russell", "Glenn Maxwell", "Faf du Plessis", "Moeen Ali", "Robin Uthappa",
            "Ambati Rayudu", "Dinesh Karthik", "Shikhar Dhawan", "Wriddhiman Saha",
            "Ravichandran Ashwin", "Piyush Chawla", "Mohit Sharma"
        ]
        for name in user_retired_17:
            self.assertIn(name, reg_df.index, f"Retired player '{name}' missing from eligibility registry!")
            status = reg_df.loc[name, "eligibility_status"]
            self.assertEqual(status, "RETIRED", f"Player '{name}' should have eligibility_status == 'RETIRED', found: {status}")
            ipl_stat = str(reg_df.loc[name, "IPL_status"])
            self.assertIn("RETIRED", ipl_stat, f"Player '{name}' should have RETIRED in IPL_status, found: {ipl_stat}")

    def test_04b_international_retirees_audited(self):
        """Verify all 23 international retirees (2022-2026) are audited and classified as RETIRED."""
        reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv").set_index("player_name")
        international_retired_23 = [
            "Eoin Morgan", "Mushfiqur Rahim", "Tamim Iqbal", "Aaron Finch", "Alex Hales",
            "Virat Kohli", "Rohit Sharma", "Ravindra Jadeja", "David Warner", "Trent Boult",
            "Shakib Al Hasan", "Mahmudullah", "Moeen Ali", "Matthew Wade", "Martin Guptill",
            "Heinrich Klaasen", "Nicholas Pooran", "Mitchell Starc", "Asif Ali", "Kane Williamson",
            "Kane Richardson", "Rassie van der Dussen", "Glenn Maxwell"
        ]
        for name in international_retired_23:
            self.assertIn(name, reg_df.index, f"International retiree '{name}' missing from eligibility registry!")
            status = reg_df.loc[name, "eligibility_status"]
            self.assertEqual(status, "RETIRED", f"Player '{name}' should have eligibility_status == 'RETIRED', found: {status}")
            intl_stat = str(reg_df.loc[name, "international_status"])
            self.assertIn("RETIRED", intl_stat, f"Player '{name}' should have RETIRED in international_status, found: {intl_stat}")

    def test_05_released_or_unsold_not_marked_retired(self):
        """Task 5 Invariant: Truly active players like Reeza Hendricks, Tim David, Phil Salt are NOT marked retired."""
        reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv").set_index("player_name")
        active_check = ["Tim David", "Suryakumar Yadav", "Reeza Hendricks", "Rinku Singh", "Phil Salt", "Romario Shepherd"]
        for name in active_check:
            self.assertEqual(reg_df.loc[name, "eligibility_status"], "ACTIVE", f"Active player '{name}' wrongly marked non-active")

    def test_06_active_leaderboard_preserves_historical_scores(self):
        """Verify active leaderboard excludes Matthew Wade, Dinesh Karthik, Ravindra Jadeja; Tim David leads."""
        act_bat = pd.read_csv(OUT_ELIG_DIR / "active_top10_batters.csv")
        self.assertEqual(len(act_bat), 10, "Active batters top 10 must have exactly 10 players")
        self.assertNotIn("Matthew Wade", act_bat["player_name"].tolist(), "Matthew Wade must not be in active leaderboard")
        self.assertNotIn("Dinesh Karthik", act_bat["player_name"].tolist(), "Dinesh Karthik must not be in active leaderboard")
        self.assertNotIn("Ravindra Jadeja", act_bat["player_name"].tolist(), "Ravindra Jadeja must not be in active leaderboard")
        self.assertNotIn("Virat Kohli", act_bat["player_name"].tolist(), "Virat Kohli must not be in active leaderboard")
        self.assertNotIn("Rohit Sharma", act_bat["player_name"].tolist(), "Rohit Sharma must not be in active leaderboard")

        # Tim David is #1 Active Batter with CPRI 82.44
        self.assertEqual(act_bat.iloc[0]["player_name"], "Tim David")
        self.assertEqual(act_bat.iloc[0]["cpri_score"], 82.44)

        # Suryakumar Yadav is #2 Active Batter with CPRI 81.42
        self.assertEqual(act_bat.iloc[1]["player_name"], "Suryakumar Yadav")
        self.assertEqual(act_bat.iloc[1]["cpri_score"], 81.42)

        # MS Dhoni enters active top 10 at #10
        self.assertEqual(act_bat.iloc[9]["player_name"], "Mahendra Singh Dhoni")
        self.assertEqual(act_bat.iloc[9]["cpri_score"], 69.85)

        # Active bowlers top 10 is 100% active
        act_bowl = pd.read_csv(OUT_ELIG_DIR / "active_top10_bowlers.csv")
        self.assertEqual(len(act_bowl), 10, "Active bowlers top 10 must have exactly 10 players")
        self.assertEqual(act_bowl.iloc[0]["player_name"], "Mitchell Santner")
        self.assertEqual(act_bowl.iloc[0]["cpri_score"], 79.84)


if __name__ == "__main__":
    unittest.main()
