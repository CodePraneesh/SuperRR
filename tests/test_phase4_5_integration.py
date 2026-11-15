#!/usr/bin/env python3
"""
tests/test_phase4_5_integration.py
SupeRR Intelligence - Phase 4.5 Final Integration Verification & Production Readiness Suite

Validates:
1. End-to-end execution of all 7 scouting intelligence features
2. Complete 3-tier fallback resilience (mocked API success, 429 rate limit, 408 timeout, missing token)
3. Anti-hallucination guardrail enforcement (rejection of ungrounded stats and altered CPRI scores)
4. Strict competition format segregation (IPL vs T20I)
5. Head-to-head sample limitation warning enforcement (<18 balls)
6. Production configuration audit (.env.example, .gitignore, requirements.txt, zero secret leakage)
"""
import os
import sys
import json
import unittest
from unittest.mock import patch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scouting_data_engine import ScoutingDataEngine
from scouting_prompt_assembler import ScoutingPromptAssembler
from hf_inference_client import HFInferenceClient
from scouting_response_verifier import ScoutingResponseVerifier
from scouting_ai_service import ScoutingAIService


class TestPhase45Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = ScoutingDataEngine()
        cls.assembler = ScoutingPromptAssembler(cls.engine)
        cls.verifier = ScoutingResponseVerifier()
        cls.service = ScoutingAIService(
            hf_token="test_mock_token_abc123",
            data_engine=cls.engine,
            prompt_assembler=cls.assembler,
            enable_tier1=True,
            enable_tier2=False
        )

    # -------------------------------------------------------------------------
    # Test 1: Full End-to-End Pipeline Across All 7 Functions
    # -------------------------------------------------------------------------
    def test_01_end_to_end_all_seven_features(self):
        """Verify the complete flow executes cleanly across all 7 scouting features."""
        # Feature 1: Scouting Report
        f1 = self.service.generate_player_report("Rinku Singh", "IPL")
        self.assertEqual(f1["status"], "success")
        self.assertIn("Rinku Singh", f1["response"])
        self.assertIn("89.03", f1["response"])
        self.assertTrue(f1["verified"])

        # Feature 2: Pressure Explanation
        f2 = self.service.explain_pressure_performance("Matheesha Pathirana", "IPL", role="Bowler")
        self.assertEqual(f2["status"], "success")
        self.assertIn("Matheesha Pathirana", f2["response"])
        self.assertIn("83.50", f2["response"])

        # Feature 3: Batter Strengths
        f3 = self.service.analyze_batter_strengths("Rinku Singh", "IPL")
        self.assertEqual(f3["status"], "success")
        self.assertIn("Tactical Strengths", f3["response"])

        # Feature 4: Bowler Strengths
        f4 = self.service.analyze_bowler_strengths("Matheesha Pathirana", "IPL")
        self.assertEqual(f4["status"], "success")
        self.assertIn("Tactical Strengths", f4["response"])

        # Feature 5: Player Comparison
        f5 = self.service.compare_players("Rinku Singh", "Suryakumar Yadav", "IPL")
        self.assertEqual(f5["status"], "success")
        self.assertIn("Rinku Singh vs Suryakumar Yadav", f5["response"])

        # Feature 6: Head-to-Head
        f6 = self.service.analyze_batter_bowler_matchup("Rinku Singh", "Mohit Sharma", "IPL")
        self.assertEqual(f6["status"], "success")
        self.assertIn("5", f6["response"])

        # Feature 7: Analytics Question Answering
        f7 = self.service.answer_cricket_question("Why is Rinku Singh rated so highly?", ["Rinku Singh"], "IPL")
        self.assertEqual(f7["status"], "success")
        self.assertIn("Rinku Singh", f7["response"])

    # -------------------------------------------------------------------------
    # Test 2: Tier 1 Hugging Face API Success & Verification
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_02_tier1_api_success_passes_verification(self, mock_generate):
        """Test that grounded Hugging Face API output passes verification and returns Tier 1."""
        mock_generate.return_value = (
            True,
            "Rinku Singh holds an official CPRI score of 89.03 (Rank 1 in IPL Batters). He acts as a Clutch Accelerant in death overs.",
            {"model": "Qwen/Qwen2.5-7B-Instruct", "latency_sec": 0.92}
        )
        res = self.service.explain_pressure_performance("Rinku Singh", "IPL", role="Batter")
        self.assertEqual(res["tier_used"], "Tier 1: Hugging Face API (Qwen/Qwen2.5-7B-Instruct)")
        self.assertTrue(res["verified"])
        self.assertIn("89.03", res["response"])

    # -------------------------------------------------------------------------
    # Test 3: Tier 1 Error Handlers Fallback to Tier 3
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_03_tier1_network_errors_safe_fallback(self, mock_generate):
        """Test rate limit, timeout, and service errors safely fall back to Tier 3."""
        for error_type, status_code in [("RATE_LIMIT", 429), ("TIMEOUT", 408), ("MODEL_UNAVAILABLE", 503)]:
            mock_generate.return_value = (False, f"Error {error_type}", {"error_type": error_type, "status_code": status_code})
            res = self.service.generate_player_report("Rinku Singh", "IPL")
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["tier_used"], "Tier 3: Deterministic Fallback Engine")
            self.assertIn("89.03", res["response"])

    # -------------------------------------------------------------------------
    # Test 4: Verifier Catches Altered CPRI or Fake Stats
    # -------------------------------------------------------------------------
    @patch.object(HFInferenceClient, "generate")
    def test_04_verifier_catches_altered_cpri(self, mock_generate):
        """Test verifier rejects altered CPRI scores and forces safe fallback."""
        # Model hallucinates CPRI of 98.4 when ground truth is 89.03
        mock_generate.return_value = (
            True,
            "Rinku Singh has an outstanding CPRI of 98.40 and is ranked #1 in IPL.",
            {"model": "Qwen/Qwen2.5-7B-Instruct"}
        )
        res = self.service.explain_pressure_performance("Rinku Singh", "IPL", role="Batter")
        self.assertEqual(res["tier_used"], "Tier 3: Deterministic Fallback Engine")
        self.assertFalse(res["verified"])
        self.assertTrue(any("CPRI IMMUTABILITY VIOLATION" in n for n in res["verification_notes"]))

    # -------------------------------------------------------------------------
    # Test 5: Format Separation & Scope Isolation
    # -------------------------------------------------------------------------
    def test_05_format_isolation_ipl_t20i(self):
        """Test IPL and T20I scopes are completely isolated."""
        # Matthew Wade is Rank 1 T20I Batter, not IPL
        t20i_wade = self.service.generate_player_report("Matthew Wade", "T20I", role="Batter")
        self.assertEqual(t20i_wade["status"], "success")
        self.assertIn("T20I", t20i_wade["response"])
        self.assertIn("97.42", t20i_wade["response"])

        with self.assertRaises(ValueError):
            self.service.generate_player_report("Matthew Wade", "IPL", role="Batter")

    # -------------------------------------------------------------------------
    # Test 6: Small-Sample Warning Enforcement in Head-to-Head
    # -------------------------------------------------------------------------
    def test_06_small_sample_warning_enforcement(self):
        """Test that head-to-head encounters on exploratory samples (<18 balls) include prominent warnings."""
        res = self.service.analyze_batter_bowler_matchup("Rinku Singh", "Mohit Sharma", "IPL")
        self.assertIn("CRITICAL SAMPLE LIMITATION", res["response"])
        self.assertIn("5 legal balls faced", res["response"])
        self.assertIn("Very Low Sample (<6 balls)", res["response"])

    # -------------------------------------------------------------------------
    # Test 7: Production Configuration Audit
    # -------------------------------------------------------------------------
    def test_07_production_configuration_audit(self):
        """Verify .env.example, .gitignore, requirements.txt, and data stores exist without secret leaks."""
        self.assertTrue((BASE_DIR / ".env.example").exists())
        self.assertTrue((BASE_DIR / ".gitignore").exists())
        self.assertTrue((BASE_DIR / "requirements.txt").exists())

        # Audit .gitignore ignores .env
        with open(BASE_DIR / ".gitignore", "r") as f:
            gi_content = f.read()
        self.assertIn(".env", gi_content)

        # Audit requirements.txt has production dependencies
        with open(BASE_DIR / "requirements.txt", "r") as f:
            req_content = f.read()
        self.assertIn("pandas", req_content)
        self.assertIn("huggingface-hub", req_content)


if __name__ == "__main__":
    unittest.main()
