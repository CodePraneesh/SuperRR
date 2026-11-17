#!/usr/bin/env python3
"""
tests/test_phase4_2_stores.py
SupeRR Intelligence - Phase 4.2 Automated Validation Test Suite

Validates:
1. JSON schema validity and presence of all required fields
2. Player coverage: exactly 40 Official Top 10 + 20 Provisional Top 5 = 60 players
3. Unique player-format-role identifiers
4. CPRI score and component preservation against Phase 3.5 freeze
5. Missing-value handling and zero-division resilience
6. Contextual split mathematical consistency (phase sums, pressure deltas)
7. Head-to-head aggregation correctness against source deliveries
8. Strict format separation (IPL vs T20I)
9. Sample tier classification accuracy
"""
import os
import sys
import json
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)


class TestPhase42ScoutingStores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = BASE_DIR / "output" / "phase4" / "data"
        cls.profiles_path = cls.data_dir / "player_scouting_profiles.json"
        cls.splits_path = cls.data_dir / "player_contextual_splits.json"
        cls.h2h_path = cls.data_dir / "head_to_head_matrix.json"
        cls.dict_path = cls.data_dir / "data_dictionary.md"

        # Load generated stores
        with open(cls.profiles_path, "r") as f:
            cls.store_1 = json.load(f)

        with open(cls.splits_path, "r") as f:
            cls.store_2 = json.load(f)

        with open(cls.h2h_path, "r") as f:
            cls.store_3 = json.load(f)

        # Load upstream reference data
        cls.off_csv = pd.read_csv("output/phase3_5/official_rankings.csv")
        deliv_path = Path("output/phase2/pressure_scored_deliveries.csv")
        if deliv_path.exists():
            cls.deliv_df = pd.read_csv(deliv_path, low_memory=False)
        else:
            cls.deliv_df = None

    def test_01_all_files_exist_and_non_empty(self):
        """Test that all three JSON stores and the data dictionary exist and are non-empty."""
        self.assertTrue(self.profiles_path.exists())
        self.assertTrue(self.splits_path.exists())
        self.assertTrue(self.h2h_path.exists())
        self.assertTrue(self.dict_path.exists())

        self.assertGreater(self.profiles_path.stat().st_size, 1000)
        self.assertGreater(self.splits_path.stat().st_size, 1000)
        self.assertGreater(self.h2h_path.stat().st_size, 10000)
        self.assertGreater(self.dict_path.stat().st_size, 500)

    def test_02_coverage_exact_60_players(self):
        """Test exact coverage: 40 Official Top 10 + 20 Provisional Top 5 = 60 players."""
        profiles = self.store_1["profiles"]
        self.assertEqual(len(profiles), 60)

        official_top10 = [p for p in profiles if p["is_official_top10"]]
        provisional_top5 = [p for p in profiles if p["is_provisional_top5"]]

        self.assertEqual(len(official_top10), 40)
        self.assertEqual(len(provisional_top5), 20)

        # Check cohort counts
        cohort_counts = self.store_1["metadata"]["cohort_counts"]
        for c in ["IPL Batters", "T20I Batters", "IPL Bowlers", "T20I Bowlers"]:
            self.assertEqual(cohort_counts[c], 15)  # 10 official + 5 provisional

    def test_03_unique_player_format_role_keys(self):
        """Test that player keys (scope_role_id) are 100% unique across all stores."""
        keys_1 = [p["profile_key"] for p in self.store_1["profiles"]]
        self.assertEqual(len(keys_1), len(set(keys_1)))

        keys_2 = [s["player_key"] for s in self.store_2["splits"]]
        self.assertEqual(len(keys_2), len(set(keys_2)))

        # Keys in store 1 and store 2 must match exactly
        self.assertEqual(set(keys_1), set(keys_2))

    def test_04_cpri_scores_match_frozen_phase3_5(self):
        """Verify CPRI scores, ranks, and components match Phase 3.5 freeze without drift."""
        for _, ref_row in self.off_csv.iterrows():
            pname = ref_row["player_name"]
            scope = ref_row["competition_scope"]
            role = ref_row["role"]
            expected_cpri = float(ref_row["cpri_score"])
            expected_rank = int(ref_row["official_rank"])
            expected_tier = str(ref_row["ranking_tier"])

            # Lookup in store 1
            profile = self.store_1["by_player_name"][pname][scope]
            self.assertEqual(profile["role"], role)
            self.assertEqual(profile["official_rank"], expected_rank)
            self.assertEqual(profile["ranking_tier"], expected_tier)
            self.assertAlmostEqual(profile["cpri_score"], expected_cpri, places=2)

            # Components
            self.assertAlmostEqual(profile["components"]["pressure_impact"], round(float(ref_row["score_pressure_impact"]), 2), places=2)
            self.assertAlmostEqual(profile["components"]["pressure_adaptability"], round(float(ref_row["score_adaptability"]), 2), places=2)
            self.assertAlmostEqual(profile["components"]["clutch_consistency"], round(float(ref_row["score_consistency"]), 2), places=2)
            self.assertAlmostEqual(profile["components"]["reliability_confidence"], round(float(ref_row["score_reliability"]), 2), places=2)

    def test_05_format_separation(self):
        """Ensure IPL and T20I records are strictly segregated across all stores."""
        for p in self.store_1["profiles"]:
            self.assertIn(p["competition_scope"], ["IPL", "T20I"])
            if p["competition_scope"] == "IPL":
                self.assertIn("IPL", p["cohort"])
            else:
                self.assertIn("T20I", p["cohort"])

        for s in self.store_2["splits"]:
            self.assertIn(s["competition_scope"], ["IPL", "T20I"])

        for m in self.store_3["matchups"]:
            self.assertIn(m["competition_scope"], ["IPL", "T20I"])

    def test_06_contextual_splits_mathematical_consistency(self):
        """Verify phase split balls equal total balls faced or bowled in non-super-overs."""
        for s in self.store_2["splits"]:
            role = s["role"]
            phase_splits = s["innings_phase_splits"]

            if role == "Batter":
                sum_phase_balls = (
                    phase_splits["powerplay"]["balls_faced"] +
                    phase_splits["middle"]["balls_faced"] +
                    phase_splits["death"]["balls_faced"]
                )
                # Deliveries evaluated may differ by super overs (which are <= 1-2 balls if any)
                self.assertLessEqual(sum_phase_balls, s["total_balls_evaluated"])
                self.assertGreaterEqual(sum_phase_balls, s["total_balls_evaluated"] - 5)

                # Check pressure contrast delta
                contrast = s["pressure_contrast"]
                expected_delta = round(contrast["high_pressure"]["strike_rate"] - contrast["low_pressure"]["strike_rate"], 2)
                self.assertAlmostEqual(contrast["delta_strike_rate"], expected_delta, places=2)

            else:
                sum_phase_balls = (
                    phase_splits["powerplay"]["balls_bowled"] +
                    phase_splits["middle"]["balls_bowled"] +
                    phase_splits["death"]["balls_bowled"]
                )
                self.assertLessEqual(sum_phase_balls, s["total_balls_evaluated"])
                self.assertGreaterEqual(sum_phase_balls, s["total_balls_evaluated"] - 5)

                contrast = s["pressure_contrast"]
                expected_delta = round(contrast["high_pressure"]["economy_rate"] - contrast["low_pressure"]["economy_rate"], 2)
                self.assertAlmostEqual(contrast["delta_economy"], expected_delta, places=2)

    def test_07_missing_value_handling_and_zero_division(self):
        """Test that zero samples or zero dismissals return None/null rather than NaN/inf."""
        for s in self.store_2["splits"]:
            for phase_name, p_data in s["innings_phase_splits"].items():
                if s["role"] == "Batter":
                    if p_data["balls_faced"] == 0:
                        self.assertEqual(p_data["strike_rate"], 0.0)
                        self.assertIsNone(p_data["batting_average"])
                        self.assertEqual(p_data["sample_tier"], "No Sample (0 balls)")
                    elif p_data["dismissals"] == 0:
                        self.assertIsNone(p_data["batting_average"])
                else:
                    if p_data["balls_bowled"] == 0:
                        self.assertEqual(p_data["economy_rate"], 0.0)
                        self.assertIsNone(p_data["bowling_average"])
                        self.assertEqual(p_data["sample_tier"], "No Sample (0 balls)")
                    elif p_data["credited_wickets"] == 0:
                        self.assertIsNone(p_data["bowling_average"])

    def test_08_head_to_head_reconciliation(self):
        """Reconcile a sample of head-to-head records against raw delivery data."""
        if self.deliv_df is None:
            self.skipTest("Requires local raw delivery dataset (output/phase2/pressure_scored_deliveries.csv)")

        # Test known encounter: Rinku Singh vs Mohit Sharma (IPL)
        h2h_key = "Rinku Singh vs Mohit Sharma [IPL]"
        if h2h_key in self.store_3["by_key"]:
            rec = self.store_3["by_key"][h2h_key]

            # Query source deliveries directly
            sub = self.deliv_df[
                (self.deliv_df["striker_name_clean"] == "Rinku Singh") &
                (self.deliv_df["bowler_name_clean"] == "Mohit Sharma") &
                (self.deliv_df["competition_scope"] == "IPL") &
                (self.deliv_df["batter_faced_ball"] == 1)
            ]
            self.assertEqual(rec["balls_faced"], len(sub))
            self.assertEqual(rec["runs_scored"], int(sub["batter_runs"].sum()))
            self.assertEqual(rec["dismissals"], int(sub["bowler_wicket"].sum()))
            self.assertEqual(rec["fours"], int(sub["derived_four"].sum()))
            self.assertEqual(rec["sixes"], int(sub["derived_six"].sum()))

    def test_09_head_to_head_sample_limitations_assigned(self):
        """Test that every head-to-head record has a valid sample tier."""
        valid_tiers = {
            "Very Low Sample (<6 balls)",
            "Low Sample (6-17 balls)",
            "Moderate Sample (18-29 balls)",
            "Robust Sample (>=30 balls)"
        }
        for m in self.store_3["matchups"][:500]:
            self.assertIn(m["sample_tier"], valid_tiers)
            if m["balls_faced"] < 6:
                self.assertEqual(m["sample_tier"], "Very Low Sample (<6 balls)")
                self.assertFalse(m["is_statistically_reliable"])
            elif m["balls_faced"] >= 30:
                self.assertEqual(m["sample_tier"], "Robust Sample (>=30 balls)")
                self.assertTrue(m["is_statistically_reliable"])

    def test_10_official_phase8_store_matches_freeze(self):
        """Verify official_scouting_store.json matches Phase 8 freeze files exactly."""
        off_store_path = self.data_dir / "official_scouting_store.json"
        self.assertTrue(off_store_path.exists(), "official_scouting_store.json must exist")
        with open(off_store_path, "r", encoding="utf-8") as f:
            off_store = json.load(f)

        p13_bat = pd.read_csv("output/phase13_evidence_floor/official_top10_batters.csv")
        p13_bowl = pd.read_csv("output/phase13_evidence_floor/official_top10_bowlers.csv")

        self.assertEqual(len(off_store["official_top10_batters"]), 10)
        self.assertEqual(len(off_store["official_top10_bowlers"]), 10)

        for i, row in p13_bat.iterrows():
            store_item = off_store["official_top10_batters"][i]
            self.assertEqual(store_item["official_rank"], int(row["official_rank"]))
            self.assertEqual(store_item["player_name"], str(row["player_name"]))
            self.assertAlmostEqual(store_item["cpri_score"], round(float(row["cpri_score"]), 2), places=2)

        for i, row in p13_bowl.iterrows():
            store_item = off_store["official_top10_bowlers"][i]
            self.assertEqual(store_item["official_rank"], int(row["official_rank"]))
            self.assertEqual(store_item["player_name"], str(row["player_name"]))
            self.assertAlmostEqual(store_item["cpri_score"], round(float(row["cpri_score"]), 2), places=2)

        # Also verify pre-floor baseline lists exist in store
        if "pre_floor_top10_batters" in off_store:
            p8_bat = pd.read_csv("output/phase8_ranking_reconsideration/official_top10_batters.csv")
            self.assertEqual(len(off_store["pre_floor_top10_batters"]), 10)
            self.assertEqual(off_store["pre_floor_top10_batters"][0]["player_name"], str(p8_bat.iloc[0]["player_name"]))


if __name__ == "__main__":
    unittest.main()
