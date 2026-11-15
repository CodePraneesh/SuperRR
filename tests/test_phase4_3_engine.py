#!/usr/bin/env python3
"""
tests/test_phase4_3_engine.py
SupeRR Intelligence - Phase 4.3 Automated Verification Suite

Validates:
1. Player retrieval by name, ID, format, and role
2. Strict format separation (IPL vs T20I)
3. Role separation (Batter vs Bowler)
4. Missing player handling (graceful None / ValueError)
5. Small-sample warnings and reliability flags
6. Frozen CPRI preservation against Phase 3.5 freeze
7. Discrepancy resolution regression test:
   - Authoritative Clutch Consistency for Rinku Singh = 56.32
   - Authoritative frozen pressure deliveries for Rinku Singh = 411
   - Authoritative frozen total deliveries = 926
   - Separation of match-state pressure deliveries from striker balls faced (387)
8. Grounded prompt assembly for all 7 scouting features
"""
import os
import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scouting_data_engine import ScoutingDataEngine
from scouting_prompt_assembler import ScoutingPromptAssembler


class TestPhase43ScoutingEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ScoutingDataEngine()
        cls.assembler = ScoutingPromptAssembler(cls.engine)

    # -------------------------------------------------------------------------
    # Test 1: Task 1 Discrepancy Resolution & Regression Test (Rinku Singh IPL)
    # -------------------------------------------------------------------------
    def test_01_rinku_singh_cpri_mapping_regression(self):
        """
        Regression Test: Resolves the two data mapping discrepancies.
        Verifies that Phase 3.5 is the authoritative source for all frozen CPRI fields:
        - Clutch Consistency = 56.32 (not 64.15)
        - Frozen Pressure Deliveries = 411 (not 269)
        - Frozen Total Deliveries = 926
        - Delivery-derived pressure balls faced is separately tracked as 387 (or 380-400)
        """
        rinku = self.engine.get_player_profile("Rinku Singh", competition_scope="IPL", role="Batter")
        self.assertIsNotNone(rinku)

        # 1. Authoritative frozen CPRI score and components
        self.assertEqual(rinku["cpri_score"], 89.03)
        self.assertEqual(rinku["components"]["pressure_impact"], 100.0)
        self.assertEqual(rinku["components"]["pressure_adaptability"], 91.55)
        self.assertEqual(rinku["components"]["clutch_consistency"], 56.32)
        self.assertEqual(rinku["components"]["reliability_confidence"], 99.22)

        # 2. Authoritative frozen exposure counts
        self.assertEqual(rinku["exposure"]["pressure_deliveries"], 411)
        self.assertEqual(rinku["exposure"]["total_deliveries"], 926)
        self.assertEqual(rinku["exposure"]["pressure_matches"], 25)

        # 3. Explicit frozen_cpri_metrics container matches
        frozen = rinku["frozen_cpri_metrics"]
        self.assertEqual(frozen["cpri_score"], 89.03)
        self.assertEqual(frozen["score_consistency"], 56.32)
        self.assertEqual(frozen["frozen_pressure_deliveries"], 411)
        self.assertEqual(frozen["frozen_total_deliveries"], 926)

        # 4. Delivery-derived stats are separate and correctly defined
        p_stats = rinku["performance_stats"]["pressure_stats"]
        self.assertIn("pressure_balls_faced", p_stats)
        self.assertGreater(p_stats["pressure_balls_faced"], 300)
        self.assertLess(p_stats["pressure_balls_faced"], 411)  # Striker balls faced is strictly < match-state deliveries due to extras

    # -------------------------------------------------------------------------
    # Test 2: Player Retrieval (Name, ID, Format, Role)
    # -------------------------------------------------------------------------
    def test_02_player_retrieval_flexibility(self):
        """Test retrieving player profile by name, ID, format, and role."""
        # By Name + Scope + Role
        p1 = self.engine.get_player_profile("Matheesha Pathirana", competition_scope="IPL", role="Bowler")
        self.assertIsNotNone(p1)
        self.assertEqual(p1["player_id"], 8661)
        self.assertEqual(p1["official_rank"], 1)

        # By ID
        p2 = self.engine.get_player_profile(player_id=8661, competition_scope="IPL")
        self.assertIsNotNone(p2)
        self.assertEqual(p2["player_name"], "Matheesha Pathirana")

        # T20I Bowler
        p3 = self.engine.get_player_profile("Sufiyan Muqeem", competition_scope="T20I", role="Bowler")
        self.assertIsNotNone(p3)
        self.assertEqual(p3["official_rank"], 1)

        # Case-insensitive name
        p4 = self.engine.get_player_profile("rinku singh", competition_scope="ipl")
        self.assertIsNotNone(p4)
        self.assertEqual(p4["player_id"], 4708)

    # -------------------------------------------------------------------------
    # Test 3: Strict Format Separation
    # -------------------------------------------------------------------------
    def test_03_format_separation(self):
        """Verify IPL and T20I records never cross or return mixed data."""
        # Player only in IPL requested in T20I
        ipl_only_batter = "Ashutosh Sharma"
        p_t20i = self.engine.get_player_profile(ipl_only_batter, competition_scope="T20I")
        self.assertIsNone(p_t20i)

        p_ipl = self.engine.get_player_profile(ipl_only_batter, competition_scope="IPL")
        self.assertIsNotNone(p_ipl)
        self.assertEqual(p_ipl["competition_scope"], "IPL")

    # -------------------------------------------------------------------------
    # Test 4: Role Separation
    # -------------------------------------------------------------------------
    def test_04_role_separation(self):
        """Verify Batter vs Bowler role queries are strictly isolated."""
        # Pathirana as Batter should return None
        p_as_bat = self.engine.get_player_profile("Matheesha Pathirana", competition_scope="IPL", role="Batter")
        self.assertIsNone(p_as_bat)

        # Pathirana as Bowler succeeds
        p_as_bowl = self.engine.get_player_profile("Matheesha Pathirana", competition_scope="IPL", role="Bowler")
        self.assertIsNotNone(p_as_bowl)
        self.assertEqual(p_as_bowl["role"], "Bowler")

    # -------------------------------------------------------------------------
    # Test 5: Missing Player Handling
    # -------------------------------------------------------------------------
    def test_05_missing_player_handling(self):
        """Verify non-existent players return None gracefully without throwing unexpected errors."""
        missing = self.engine.get_player_profile("NonExistent Player 999", competition_scope="IPL")
        self.assertIsNone(missing)

        splits = self.engine.get_contextual_splits("NonExistent Player 999", competition_scope="IPL")
        self.assertIsNone(splits)

        with self.assertRaises(ValueError):
            self.engine.compare_batters("NonExistent Player A", "Rinku Singh", competition_scope="IPL")

    # -------------------------------------------------------------------------
    # Test 6: Small-Sample Warnings & Head-to-Head Reliability
    # -------------------------------------------------------------------------
    def test_06_small_sample_and_h2h_reliability(self):
        """Verify sample limitation flags and reliability thresholds."""
        # 5-ball encounter: Rinku Singh vs Mohit Sharma
        h2h = self.engine.get_head_to_head("Rinku Singh", "Mohit Sharma", competition_scope="IPL")
        self.assertIsNotNone(h2h)
        self.assertEqual(h2h["balls_faced"], 5)
        self.assertEqual(h2h["sample_tier"], "Very Low Sample (<6 balls)")
        self.assertFalse(h2h["is_statistically_reliable"])

        # Zero-ball encounter returns structured zero-sample dict
        h2h_zero = self.engine.get_head_to_head("Rinku Singh", "Jasprit Bumrah", competition_scope="T20I")
        self.assertEqual(h2h_zero["balls_faced"], 0)
        self.assertFalse(h2h_zero["is_statistically_reliable"])
        self.assertEqual(h2h_zero["sample_tier"], "No Historical Encounters (0 balls)")

    # -------------------------------------------------------------------------
    # Test 7: Batter Comparison Engine
    # -------------------------------------------------------------------------
    def test_07_compare_batters_matrix(self):
        """Verify comparative analysis between two batters."""
        comp = self.engine.compare_batters("Rinku Singh", "Suryakumar Yadav", competition_scope="IPL")
        self.assertIn("deltas_a_minus_b", comp)
        self.assertIn("phase_comparison", comp)
        self.assertEqual(comp["batter_a"]["name"], "Rinku Singh")
        self.assertEqual(comp["batter_b"]["name"], "Suryakumar Yadav")

        # Rinku CPRI is 89.03, Suryakumar is 88.41 in IPL
        expected_cpri_delta = round(89.03 - 88.41, 2)
        self.assertAlmostEqual(comp["deltas_a_minus_b"]["cpri_delta"], expected_cpri_delta, places=2)

    # -------------------------------------------------------------------------
    # Test 8: Strengths & Weaknesses Extraction
    # -------------------------------------------------------------------------
    def test_08_strengths_and_weaknesses(self):
        """Verify empirical strengths and weaknesses extraction."""
        sw_rinku = self.engine.get_strengths_and_weaknesses("Rinku Singh", competition_scope="IPL")
        self.assertIn("strengths", sw_rinku)
        self.assertIn("weaknesses", sw_rinku)
        # Rinku has an elite death strike rate (>175 SR), so should have death finisher strength
        strengths_str = " ".join(sw_rinku["strengths"])
        self.assertIn("Death", strengths_str)

        sw_pathi = self.engine.get_strengths_and_weaknesses("Matheesha Pathirana", competition_scope="IPL")
        self.assertIn("strengths", sw_pathi)
        pathi_str = " ".join(sw_pathi["strengths"])
        self.assertIn("Death", pathi_str)

    # -------------------------------------------------------------------------
    # Test 9: Grounded Prompt Assembler (All 7 Features)
    # -------------------------------------------------------------------------
    def test_09_grounded_prompt_assembler(self):
        """Verify prompt generation across all 7 core scouting features."""
        # 1. Scouting Report
        p1 = self.assembler.build_scouting_report_prompt("Rinku Singh", "IPL")
        self.assertEqual(p1["feature"], "player_scouting_report")
        self.assertIn("=== SYSTEM DIRECTIVE ===", p1["assembled_prompt"])
        self.assertIn("Rinku Singh", p1["assembled_prompt"])
        self.assertIn("89.03", p1["assembled_prompt"])

        # 2. Pressure Explanation
        p2 = self.assembler.build_pressure_explanation_prompt("Rinku Singh", "IPL")
        self.assertEqual(p2["feature"], "pressure_performance_explanation")
        self.assertIn("pressure_analysis", p2["evidence_payload"])

        # 3. Batter Strengths and Weaknesses
        p3 = self.assembler.build_batter_strengths_weaknesses_prompt("Rinku Singh", "IPL")
        self.assertEqual(p3["feature"], "batter_strengths_weaknesses")
        self.assertIn("strengths_evidence", p3["evidence_payload"])

        # 4. Bowler Strengths and Weaknesses
        p4 = self.assembler.build_bowler_strengths_weaknesses_prompt("Matheesha Pathirana", "IPL")
        self.assertEqual(p4["feature"], "bowler_strengths_weaknesses")
        self.assertIn("strengths_evidence", p4["evidence_payload"])

        # 5. Batter Comparison
        p5 = self.assembler.build_batter_comparison_prompt("Rinku Singh", "Suryakumar Yadav", "IPL")
        self.assertEqual(p5["feature"], "batter_comparison")
        self.assertIn("deltas_a_minus_b", p5["evidence_payload"])

        # 6. Batter vs Bowler Head-to-Head
        p6 = self.assembler.build_h2h_scouting_prompt("Rinku Singh", "Mohit Sharma", "IPL")
        self.assertEqual(p6["feature"], "head_to_head_scouting")
        self.assertTrue(len(p6["sample_limitations"]) > 0)  # Must include limitation for 5 balls

        # 7. Natural Language Analytics
        p7 = self.assembler.build_analytics_qa_prompt("Who is the top death overs bowler?", ["Matheesha Pathirana"], "IPL")
        self.assertEqual(p7["feature"], "natural_language_analytics")
        self.assertIn("Matheesha Pathirana", p7["evidence_payload"]["entity_profiles"])


if __name__ == "__main__":
    unittest.main()
