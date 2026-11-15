"""
tests/test_ppr_ranking.py
Unit and integration tests for Pressure Performance Reliability (PPR),
Sample Size Evidence Classification, and Volume-Adjusted CPRI Engine.
"""
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from ml.ppr_engine import (
    EvidenceTierConfig,
    calculate_ppr,
    calculate_adjusted_cpri,
    calculate_role_success_norm,
    enrich_player_with_ppr_and_adjustment,
    compute_batter_role_metrics,
    compute_bowler_role_metrics
)


class TestEvidenceTierClassification(unittest.TestCase):
    """Test configurable sample size evidence tier classifications."""

    def setUp(self):
        self.config = EvidenceTierConfig()

    def test_default_tier_classification(self):
        # Elite Evidence (600+)
        self.assertEqual(self.config.classify(600), "Elite Evidence")
        self.assertEqual(self.config.classify(749), "Elite Evidence")
        self.assertEqual(self.config.classify(970), "Elite Evidence")

        # Strong Evidence (400-599)
        self.assertEqual(self.config.classify(400), "Strong Evidence")
        self.assertEqual(self.config.classify(476), "Strong Evidence")
        self.assertEqual(self.config.classify(599), "Strong Evidence")

        # Moderate Evidence (250-399)
        self.assertEqual(self.config.classify(250), "Moderate Evidence")
        self.assertEqual(self.config.classify(378), "Moderate Evidence")
        self.assertEqual(self.config.classify(399), "Moderate Evidence")

        # Limited Evidence (150-249)
        self.assertEqual(self.config.classify(150), "Limited Evidence")
        self.assertEqual(self.config.classify(191), "Limited Evidence")
        self.assertEqual(self.config.classify(249), "Limited Evidence")

        # Insufficient Evidence (<150)
        self.assertEqual(self.config.classify(149), "Insufficient Evidence")
        self.assertEqual(self.config.classify(50), "Insufficient Evidence")
        self.assertEqual(self.config.classify(0), "Insufficient Evidence")

    def test_custom_configurable_thresholds(self):
        custom_config = EvidenceTierConfig(
            elite_threshold=500,
            strong_threshold=300,
            moderate_threshold=200,
            limited_threshold=100
        )
        self.assertEqual(custom_config.classify(520), "Elite Evidence")
        self.assertEqual(custom_config.classify(350), "Strong Evidence")
        self.assertEqual(custom_config.classify(220), "Moderate Evidence")
        self.assertEqual(custom_config.classify(120), "Limited Evidence")
        self.assertEqual(custom_config.classify(80), "Insufficient Evidence")

    def test_main_leaderboard_eligibility(self):
        # Requires >= 400 balls
        self.assertTrue(self.config.is_main_eligible(400))
        self.assertTrue(self.config.is_main_eligible(749))
        self.assertFalse(self.config.is_main_eligible(399))
        self.assertFalse(self.config.is_main_eligible(191))
        self.assertFalse(self.config.is_main_eligible(150))


class TestPPRMetricFormulation(unittest.TestCase):
    """Test Pressure Performance Reliability (PPR) mathematical properties."""

    def test_ppr_boundedness(self):
        # Minimum score bounded at 0, max at 100
        low_ppr = calculate_ppr(
            pressure_deliveries=1000,
            score_pressure_impact=0.0,
            score_adaptability=0.0,
            score_consistency=0.0,
            success_rate_pct=0.0,
            role="Batter"
        )
        self.assertGreaterEqual(low_ppr, 0.0)

        high_ppr = calculate_ppr(
            pressure_deliveries=1000,
            score_pressure_impact=100.0,
            score_adaptability=100.0,
            score_consistency=100.0,
            success_rate_pct=100.0,
            role="Batter"
        )
        self.assertLessEqual(high_ppr, 100.0)

    def test_low_volume_regresses_toward_baseline(self):
        # A player with inflated rate stats over very few deliveries regresses towards neutral 50.0
        small_sample_ppr = calculate_ppr(
            pressure_deliveries=10,
            score_pressure_impact=95.0,
            score_adaptability=95.0,
            score_consistency=95.0,
            success_rate_pct=40.0,
            role="Batter"
        )
        # Should be shrunk heavily towards 50.0
        self.assertLess(small_sample_ppr, 55.0)

    def test_volume_does_not_compensate_for_poor_performance(self):
        # High-volume player with poor clutch skills stays below 50.0
        poor_high_vol_ppr = calculate_ppr(
            pressure_deliveries=800,
            score_pressure_impact=35.0,
            score_adaptability=35.0,
            score_consistency=35.0,
            success_rate_pct=18.0,
            role="Batter"
        )
        self.assertLess(poor_high_vol_ppr, 50.0)

        # Confirm that a better performer with 450 balls beats the poor performer with 800 balls
        good_mid_vol_ppr = calculate_ppr(
            pressure_deliveries=450,
            score_pressure_impact=75.0,
            score_adaptability=75.0,
            score_consistency=70.0,
            success_rate_pct=32.0,
            role="Batter"
        )
        self.assertGreater(good_mid_vol_ppr, poor_high_vol_ppr)


class TestVolumeAdjustedCPRI(unittest.TestCase):
    """Test Volume-Adjusted CPRI and diagnostic leaderboard order."""

    def test_diagnostic_batters_order(self):
        """
        Verify that Matthew Wade (191 balls) drops below Suryakumar Yadav (749 balls)
        and Tim David (476 balls) on Adjusted CPRI.
        """
        # Matthew Wade: 191 balls, high raw scores
        wade_ppr = calculate_ppr(
            pressure_deliveries=191,
            score_pressure_impact=89.98,
            score_adaptability=94.81,
            score_consistency=89.38,
            success_rate_pct=36.13,
            role="Batter"
        )
        wade_adj = calculate_adjusted_cpri(
            pressure_deliveries=191,
            score_pressure_impact=89.98,
            score_adaptability=94.81,
            score_consistency=89.38,
            score_reliability=51.96,
            ppr_score=wade_ppr
        )

        # Suryakumar Yadav: 749 balls, elite high-volume clutch pillar
        surya_ppr = calculate_ppr(
            pressure_deliveries=749,
            score_pressure_impact=78.09,
            score_adaptability=74.65,
            score_consistency=85.57,
            success_rate_pct=31.24,
            role="Batter"
        )
        surya_adj = calculate_adjusted_cpri(
            pressure_deliveries=749,
            score_pressure_impact=78.09,
            score_adaptability=74.65,
            score_consistency=85.57,
            score_reliability=96.02,
            ppr_score=surya_ppr
        )

        # Tim David: 476 balls, strong-volume clutch accelerant
        david_ppr = calculate_ppr(
            pressure_deliveries=476,
            score_pressure_impact=85.07,
            score_adaptability=84.16,
            score_consistency=70.39,
            success_rate_pct=31.72,
            role="Batter"
        )
        david_adj = calculate_adjusted_cpri(
            pressure_deliveries=476,
            score_pressure_impact=85.07,
            score_adaptability=84.16,
            score_consistency=70.39,
            score_reliability=88.64,
            ppr_score=david_ppr
        )

        # Surya and Tim David MUST outrank Wade on Adjusted CPRI
        self.assertGreater(surya_adj, wade_adj, f"Surya ({surya_adj}) must beat Wade ({wade_adj})")
        self.assertGreater(david_adj, wade_adj, f"Tim David ({david_adj}) must beat Wade ({wade_adj})")

    def test_diagnostic_bowlers_order(self):
        """
        Verify that Sufiyan Muqeem (151 balls) and Jamie Overton (168 balls)
        drop below Rashid Khan (970 balls) and Mitchell Santner (653 balls).
        """
        # Sufiyan Muqeem: 151 balls
        muqeem_ppr = calculate_ppr(
            pressure_deliveries=151,
            score_pressure_impact=85.47,
            score_adaptability=88.85,
            score_consistency=82.02,
            success_rate_pct=72.19,
            role="Bowler"
        )
        muqeem_adj = calculate_adjusted_cpri(
            pressure_deliveries=151,
            score_pressure_impact=85.47,
            score_adaptability=88.85,
            score_consistency=82.02,
            score_reliability=39.85,
            ppr_score=muqeem_ppr
        )

        # Rashid Khan: 970 balls
        rashid_ppr = calculate_ppr(
            pressure_deliveries=970,
            score_pressure_impact=75.35,
            score_adaptability=74.09,
            score_consistency=71.95,
            success_rate_pct=60.93,
            role="Bowler"
        )
        rashid_adj = calculate_adjusted_cpri(
            pressure_deliveries=970,
            score_pressure_impact=75.35,
            score_adaptability=74.09,
            score_consistency=71.95,
            score_reliability=99.00,
            ppr_score=rashid_ppr
        )

        # Mitchell Santner: 653 balls
        santner_ppr = calculate_ppr(
            pressure_deliveries=653,
            score_pressure_impact=76.48,
            score_adaptability=79.15,
            score_consistency=76.45,
            success_rate_pct=58.50,
            role="Bowler"
        )
        santner_adj = calculate_adjusted_cpri(
            pressure_deliveries=653,
            score_pressure_impact=76.48,
            score_adaptability=79.15,
            score_consistency=76.45,
            score_reliability=94.45,
            ppr_score=santner_ppr
        )

        self.assertGreater(rashid_adj, muqeem_adj, f"Rashid ({rashid_adj}) must beat Muqeem ({muqeem_adj})")
        self.assertGreater(santner_adj, muqeem_adj, f"Santner ({santner_adj}) must beat Muqeem ({muqeem_adj})")


class TestScoutingStoreIntegrity(unittest.TestCase):
    """Test that official_scouting_store.json contains all required fields and partitions."""

    def test_store_structure_and_eligibility(self):
        import json
        store_path = Path("output/phase4/data/official_scouting_store.json")
        self.assertTrue(store_path.exists(), "official_scouting_store.json must exist")

        with open(store_path, "r", encoding="utf-8") as f:
            store = json.load(f)

        # Verify key sections
        self.assertIn("main_leaderboard_batters", store)
        self.assertIn("main_leaderboard_bowlers", store)
        self.assertIn("contender_batters", store)
        self.assertIn("contender_bowlers", store)

        # Verify all main leaderboard players have >= 400 pressure balls
        for b in store["main_leaderboard_batters"]:
            p_balls = b["pressure_stats"]["pressure_deliveries"]
            self.assertGreaterEqual(p_balls, 400, f"{b['player_name']} in Main Leaderboard has {p_balls} < 400")
            self.assertTrue(b["is_main_eligible"])
            self.assertEqual(b["eligibility_status"], "Main Leaderboard")
            self.assertIn(b["evidence_tier"], ["Elite Evidence", "Strong Evidence"])

        for bw in store["main_leaderboard_bowlers"]:
            p_balls = bw["pressure_stats"]["pressure_deliveries"]
            self.assertGreaterEqual(p_balls, 400, f"{bw['player_name']} in Main Leaderboard has {p_balls} < 400")
            self.assertTrue(bw["is_main_eligible"])
            self.assertEqual(bw["eligibility_status"], "Main Leaderboard")
            self.assertIn(bw["evidence_tier"], ["Elite Evidence", "Strong Evidence"])

        # Verify contenders have < 400 and >= 150 pressure balls
        for b in store["contender_batters"]:
            p_balls = b["pressure_stats"]["pressure_deliveries"]
            self.assertLess(p_balls, 400, f"{b['player_name']} in Contenders has {p_balls} >= 400")
            self.assertGreaterEqual(p_balls, 150)
            self.assertFalse(b["is_main_eligible"])
            self.assertEqual(b["eligibility_status"], "Contender / Emerging")


if __name__ == "__main__":
    unittest.main()
