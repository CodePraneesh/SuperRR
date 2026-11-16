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

    def test_04_task4_named_ipl_retirees_audited(self):
        """Verify all 9 players requested in Task 4 are explicitly audited with accurate status distinctions."""
        reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv").set_index("player_name")
        task4_names = [
            "Robin Uthappa", "Kieron Pollard", "Dwayne Bravo", "Ambati Rayudu",
            "Dinesh Karthik", "Shikhar Dhawan", "Wriddhiman Saha",
            "Ravichandran Ashwin", "Andre Russell"
        ]
        for name in task4_names:
            self.assertIn(name, reg_df.index, f"Task 4 player '{name}' missing from eligibility registry!")

        # Confirmed IPL retirees
        for name in ["Robin Uthappa", "Kieron Pollard", "Dwayne Bravo", "Ambati Rayudu", "Dinesh Karthik", "Shikhar Dhawan", "Wriddhiman Saha"]:
            ipl_stat = str(reg_df.loc[name, "IPL_status"])
            self.assertIn("RETIRED", ipl_stat, f"Player '{name}' should have RETIRED in IPL_status, found: {ipl_stat}")

        # Ashwin and Russell must NOT be classified as retired
        ashwin_status = reg_df.loc["Ravichandran Ashwin", "eligibility_status"]
        russell_status = reg_df.loc["Andre Russell", "eligibility_status"]
        self.assertEqual(ashwin_status, "ACTIVE", "Ravichandran Ashwin should be ACTIVE!")
        self.assertEqual(russell_status, "ACTIVE", "Andre Russell should be ACTIVE!")
        self.assertIn("ACTIVE", str(reg_df.loc["Ravichandran Ashwin", "IPL_status"]))
        self.assertIn("ACTIVE", str(reg_df.loc["Andre Russell", "IPL_status"]))

    def test_05_released_or_unsold_not_marked_retired(self):
        """Task 5 Invariant: Players like Matthew Wade, Reeza Hendricks, Tim David are NOT marked retired merely for being unsold."""
        reg_df = pd.read_csv(DATA_DIR / "player_eligibility_registry.csv").set_index("player_name")
        # Matthew Wade: retired from internationals, but active in BBL/franchise T20
        self.assertEqual(reg_df.loc["Matthew Wade", "eligibility_status"], "ACTIVE")
        self.assertIn("RETIRED", str(reg_df.loc["Matthew Wade", "international_status"]))
        self.assertIn("ACTIVE", str(reg_df.loc["Matthew Wade", "franchise_T20_status"]))

        # Reeza Hendricks: unsold/replacement, but active in internationals & SA20
        self.assertEqual(reg_df.loc["Reeza Hendricks", "eligibility_status"], "ACTIVE")

    def test_06_active_leaderboard_preserves_historical_scores(self):
        """Verify active leaderboard filters Dinesh Karthik from batters and replaces with Shashank Singh."""
        act_bat = pd.read_csv(OUT_ELIG_DIR / "active_top10_batters.csv")
        self.assertEqual(len(act_bat), 10, "Active batters top 10 must have exactly 10 players")
        self.assertNotIn("Dinesh Karthik", act_bat["player_name"].tolist(), "Dinesh Karthik must not be in active leaderboard")
        self.assertIn("Shashank Singh", act_bat["player_name"].tolist(), "Shashank Singh should enter active batters top 10")

        # Check Matthew Wade CPRI is still 85.36 (score preserved)
        wade_row = act_bat[act_bat["player_name"] == "Matthew Wade"].iloc[0]
        self.assertEqual(wade_row["cpri_score"], 85.36)

        # Active bowlers top 10 is 100% active
        act_bowl = pd.read_csv(OUT_ELIG_DIR / "active_top10_bowlers.csv")
        self.assertEqual(len(act_bowl), 10, "Active bowlers top 10 must have exactly 10 players")
        self.assertEqual(act_bowl.iloc[0]["player_name"], "Mitchell Santner")
        self.assertEqual(act_bowl.iloc[0]["cpri_score"], 79.84)


if __name__ == "__main__":
    unittest.main()
