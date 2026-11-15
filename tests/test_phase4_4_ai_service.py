#!/usr/bin/env python3
"""
tests/test_phase4_4_ai_service.py
SupeRR Intelligence - Phase 4.4 Automated AI Generation Service Test Suite

Validates:
1. API success with mocked responses (Tier 1 attribution)
2. API failure modes: Missing token, Timeout, Rate limiting (HTTP 429) -> Graceful Tier 3 fallback
3. Offline deterministic fallback generation (100% offline uptime)
4. Evidence verification & CPRI immutability (rejects altered CPRI or false ranks)
5. Format separation & entity integrity (IPL vs T20I)
6. Small-sample warning enforcement (discloses exploratory sample caveats)
7. Full operational execution of all seven generation functions
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scouting_data_engine import ScoutingDataEngine
from scouting_prompt_assembler import ScoutingPromptAssembler
from hf_inference_client import HFInferenceClient
from scouting_response_verifier import ScoutingResponseVerifier
from scouting_ai_service import ScoutingAIService, DeterministicScoutingFallback


class TestPhase44AIService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ScoutingDataEngine()
        cls.assembler = ScoutingPromptAssembler(cls.engine)
        cls.verifier = ScoutingResponseVerifier()
        # Initialize service with Tier 1 enabled (will be mocked)
        cls.service = ScoutingAIService(
            hf_token="mock_valid_token_12345",
            data_engine=cls.engine,
            prompt_assembler=cls.assembler,
            enable_tier1=True
        )

    # -------------------------------------------------------------------------
    # Test 1: Mocked API Success & Tier 1 Attribution
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_01_api_success_tier1_attribution(self, mock_generate):
        """Test successful Hugging Face API call passing evidence verification."""
        mock_generate.return_value = (
            True,
            "Rinku Singh holds an official CPRI of 89.03 (Rank 1 in IPL Batters). He demonstrates elite death overs acceleration.",
            {"model": "Qwen/Qwen2.5-7B-Instruct", "latency_sec": 0.85, "finish_reason": "stop"}
        )

        res = self.service.explain_pressure_performance("Rinku Singh", "IPL", role="Batter")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tier_used"], "Tier 1: Hugging Face API (Qwen/Qwen2.5-7B-Instruct)")
        self.assertTrue(res["verified"])
        self.assertIn("Rinku Singh", res["response"])
        self.assertIn("89.03", res["response"])

    # -------------------------------------------------------------------------
    # Test 2: Missing Token Fallback
    # -------------------------------------------------------------------------
    def test_02_missing_token_fallback(self):
        """Test missing HF_TOKEN falls back gracefully to Tier 3 without error."""
        service_no_token = ScoutingAIService(hf_token=None, enable_tier1=True)
        res = service_no_token.generate_player_report("Rinku Singh", "IPL")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tier_used"], "Tier 3: Deterministic Fallback Engine")
        self.assertIn("Rinku Singh", res["response"])
        self.assertIn("89.03", res["response"])

    # -------------------------------------------------------------------------
    # Test 3: API Timeout & Rate Limiting Fallback
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_03_timeout_and_rate_limit_fallback(self, mock_generate):
        """Test API rate limit (429) and timeout trigger safe fallback to Tier 3."""
        # 1. Rate Limit
        mock_generate.return_value = (
            False,
            "Hugging Face API rate limit reached (HTTP 429).",
            {"error_type": "RATE_LIMIT", "status_code": 429}
        )
        res_rate = self.service.generate_player_report("Matheesha Pathirana", "IPL", role="Bowler")
        self.assertEqual(res_rate["status"], "success")
        self.assertEqual(res_rate["tier_used"], "Tier 3: Deterministic Fallback Engine")
        self.assertIn("Matheesha Pathirana", res_rate["response"])

        # 2. Timeout
        mock_generate.return_value = (
            False,
            "Request to Hugging Face timed out after 25.0s.",
            {"error_type": "TIMEOUT", "status_code": 408}
        )
        res_timeout = self.service.generate_player_report("Matheesha Pathirana", "IPL", role="Bowler")
        self.assertEqual(res_timeout["status"], "success")
        self.assertEqual(res_timeout["tier_used"], "Tier 3: Deterministic Fallback Engine")

    # -------------------------------------------------------------------------
    # Test 4: Evidence Verification & CPRI Immutability Violation Rejection
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_04_cpri_immutability_violation_caught(self, mock_generate):
        """Test verifier detects altered CPRI scores and rejects them in favor of safe fallback."""
        # Model hallucinates CPRI of 97.5 when ground truth is 89.03
        mock_generate.return_value = (
            True,
            "Rinku Singh is exceptional with an updated CPRI of 97.5 points and rank #2.",
            {"model": "Qwen/Qwen2.5-7B-Instruct"}
        )

        res = self.service.explain_pressure_performance("Rinku Singh", "IPL", role="Batter")
        self.assertEqual(res["status"], "success")
        # Must reject ungrounded claim and use verified fallback
        self.assertEqual(res["tier_used"], "Tier 3: Deterministic Fallback Engine")
        self.assertFalse(res["verified"])
        self.assertTrue(any("CPRI IMMUTABILITY VIOLATION" in v for v in res["verification_notes"]))
        # Ground truth CPRI must be preserved in response
        self.assertIn("89.03", res["response"])

    # -------------------------------------------------------------------------
    # Test 5: Format Separation & Entity Integrity
    # -------------------------------------------------------------------------
    def test_05_format_separation(self):
        """Verify format separation is strictly enforced in generation."""
        # Query Matthew Wade in T20I
        res_t20i = self.service.generate_player_report("Matthew Wade", "T20I", role="Batter")
        self.assertEqual(res_t20i["status"], "success")
        self.assertIn("T20I", res_t20i["response"])
        self.assertIn("Matthew Wade", res_t20i["response"])

        # Query Matthew Wade in IPL (not a ranked IPL batter)
        with self.assertRaises(ValueError):
            self.service.generate_player_report("Matthew Wade", "IPL", role="Batter")

    # -------------------------------------------------------------------------
    # Test 6: Small-Sample Warnings & Head-to-Head Reliability
    # -------------------------------------------------------------------------
    def test_06_small_sample_warning_enforcement(self):
        """Test that head-to-head encounters on low samples (<18 balls) include prominent warnings."""
        res_h2h = self.service.analyze_batter_bowler_matchup("Rinku Singh", "Mohit Sharma", "IPL")
        self.assertEqual(res_h2h["status"], "success")
        self.assertIn("Rinku Singh vs Mohit Sharma", res_h2h["response"])
        self.assertIn("5", res_h2h["response"])  # 5 balls
        self.assertIn("CRITICAL SAMPLE LIMITATION", res_h2h["response"])
        self.assertIn("Very Low Sample (<6 balls)", res_h2h["response"])

    # -------------------------------------------------------------------------
    # Test 7: Full Execution of All Seven Generation Functions
    # -------------------------------------------------------------------------
    def test_07_all_seven_scouting_features_execute(self):
        """Verify all seven generation methods execute cleanly and produce populated markdown."""
        # 1. Player Report
        f1 = self.service.generate_player_report("Rinku Singh", "IPL")
        self.assertEqual(f1["feature"], "player_scouting_report")
        self.assertGreater(len(f1["response"]), 200)

        # 2. Pressure Explanation
        f2 = self.service.explain_pressure_performance("Matheesha Pathirana", "IPL", role="Bowler")
        self.assertEqual(f2["feature"], "pressure_performance_explanation")
        self.assertGreater(len(f2["response"]), 200)

        # 3. Batter Strengths
        f3 = self.service.analyze_batter_strengths("Rinku Singh", "IPL")
        self.assertEqual(f3["feature"], "batter_strengths_weaknesses")
        self.assertGreater(len(f3["response"]), 150)

        # 4. Bowler Strengths
        f4 = self.service.analyze_bowler_strengths("Matheesha Pathirana", "IPL")
        self.assertEqual(f4["feature"], "bowler_strengths_weaknesses")
        self.assertGreater(len(f4["response"]), 150)

        # 5. Batter Comparison
        f5 = self.service.compare_players("Rinku Singh", "Suryakumar Yadav", "IPL")
        self.assertEqual(f5["feature"], "batter_comparison")
        self.assertGreater(len(f5["response"]), 250)

        # 6. Batter vs Bowler H2H
        f6 = self.service.analyze_batter_bowler_matchup("Rinku Singh", "Mohit Sharma", "IPL")
        self.assertEqual(f6["feature"], "head_to_head_scouting")
        self.assertGreater(len(f6["response"]), 150)

        # 7. Natural Language QA
        f7 = self.service.answer_cricket_question("Why is Rinku Singh rated so highly?", ["Rinku Singh"], "IPL")
        self.assertEqual(f7["feature"], "natural_language_analytics")
        self.assertGreater(len(f7["response"]), 100)


if __name__ == "__main__":
    unittest.main()
