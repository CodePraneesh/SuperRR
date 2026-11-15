#!/usr/bin/env python3
"""
tests/test_scouting_verifier_adversarial.py
Adversarial test suite for ScoutingResponseVerifier guardrails.
Verifies rejection of:
1. Wrong ranks (including ranks 1, 5, 10 previously exempted)
2. Ordinal rank mismatches ('3rd', 'first', 'number 2')
3. Ungrounded CPRI scores beyond tolerance
4. Small sample matchups (<18 balls) without explicit sample size or caveat
5. Format confusion (claiming IPL is T20I or vice versa)
6. Unsubstantiated dominance claims on micro-samples
"""
import unittest
from scouting_response_verifier import ScoutingResponseVerifier


class TestScoutingVerifierAdversarial(unittest.TestCase):

    def setUp(self):
        self.verifier = ScoutingResponseVerifier(tolerance=0.25)

        # Baseline ground truth evidence for Suryakumar Yadav (Official Rank #3, CPRI 81.42)
        self.sky_evidence = {
            "player_name": "Suryakumar Yadav",
            "competition_scope": "IPL",
            "role": "Batter",
            "official_rank": 3,
            "cpri_score": 81.42,
            "components": {
                "pressure_impact": 78.09,
                "pressure_adaptability": 74.65,
                "clutch_consistency": 81.25,
                "reliability_confidence": 98.50
            }
        }

        # Small-sample head-to-head evidence (8 balls)
        self.h2h_small_sample_evidence = {
            "head_to_head_record": {
                "batter_name": "Rinku Singh",
                "bowler_name": "Trent Boult",
                "balls_faced": 8,
                "runs_scored": 14,
                "dismissals": 0,
                "is_statistically_reliable": False
            },
            "competition_scope": "IPL"
        }

    def test_01_valid_ground_truth_passes(self):
        """Valid response with exact rank, CPRI, and scope must pass cleanly."""
        text = "Suryakumar Yadav has an official CPRI of 81.42 and is ranked #3 among batters in IPL."
        is_valid, violations = self.verifier.verify_response(text, self.sky_evidence)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_02_wrong_rank_1_5_10_rejected_without_exemption(self):
        """Verifies that claiming rank 1, 5, or 10 for a rank #3 player is strictly rejected."""
        # Claiming rank 1 (previously exempted by bug)
        text_rank_1 = "Suryakumar Yadav is rank 1 with CPRI score 81.42."
        is_valid, violations = self.verifier.verify_response(text_rank_1, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("RANK INTEGRITY VIOLATION" in v and "rank 1" in v for v in violations))

        # Claiming rank 5
        text_rank_5 = "Suryakumar Yadav is ranked #5 with CPRI 81.42."
        is_valid, violations = self.verifier.verify_response(text_rank_5, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("RANK INTEGRITY VIOLATION" in v and "rank 5" in v for v in violations))

        # Claiming rank 10
        text_rank_10 = "Suryakumar Yadav holds rank 10 with CPRI 81.42."
        is_valid, violations = self.verifier.verify_response(text_rank_10, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("RANK INTEGRITY VIOLATION" in v and "rank 10" in v for v in violations))

    def test_03_ordinal_rank_parsing_catches_wrong_rank(self):
        """Verifies that ordinal phrases ('first', '1st', '3rd', 'second') are parsed and audited."""
        # Player is rank 3; model says 'first'
        text_ordinal_wrong = "Suryakumar Yadav is the first ranked batter with CPRI 81.42."
        is_valid, violations = self.verifier.verify_response(text_ordinal_wrong, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("RANK INTEGRITY VIOLATION" in v for v in violations))

        # Model says '3rd' which matches rank 3
        text_ordinal_correct = "Suryakumar Yadav is the 3rd ranked batter with CPRI 81.42."
        is_valid, violations = self.verifier.verify_response(text_ordinal_correct, self.sky_evidence)
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_04_wrong_cpri_beyond_tolerance_rejected(self):
        """Verifies that hallucinated or altered CPRI scores are rejected using self.tolerance."""
        # True score is 81.42. Model claims 81.45 (within 0.25 tolerance) -> PASS
        text_close = "CPRI score: 81.45."
        is_valid, _ = self.verifier.verify_response(text_close, self.sky_evidence)
        self.assertTrue(is_valid)

        # Model claims 82.50 (outside 0.25 tolerance) -> REJECT
        text_far = "CPRI score: 82.50."
        is_valid, violations = self.verifier.verify_response(text_far, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("CPRI IMMUTABILITY VIOLATION" in v for v in violations))

    def test_05_small_sample_missing_caveat_rejected(self):
        """Verifies that low-sample matchups (<18 balls) lacking explicit sample caveats are rejected."""
        # Text discusses the matchup but has no sample caveat
        text_no_caveat = "Rinku Singh scored 14 runs against Trent Boult without being dismissed."
        is_valid, violations = self.verifier.verify_response(text_no_caveat, self.h2h_small_sample_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("SMALL SAMPLE WARNING VIOLATION" in v for v in violations))

        # Text with explicit ball count or small sample caveat passes
        text_with_caveat = "Over a small sample of 8 balls, Rinku Singh has scored 14 runs against Trent Boult."
        is_valid, violations = self.verifier.verify_response(text_with_caveat, self.h2h_small_sample_evidence)
        self.assertTrue(is_valid)

    def test_06_unsubstantiated_dominance_claim_on_small_sample_rejected(self):
        """Verifies that claiming dominance on small samples is rejected."""
        text_dominance = "Rinku Singh completely dominates Trent Boult across 8 balls."
        is_valid, violations = self.verifier.verify_response(text_dominance, self.h2h_small_sample_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("UNGROUNDED TACTICAL CLAIM" in v for v in violations))

    def test_07_format_confusion_rejected(self):
        """Verifies that conflating IPL and T20I scope triggers a format violation."""
        text_wrong_format = "Suryakumar Yadav has shown excellence across T20 International matches with CPRI 81.42 in T20I."
        is_valid, violations = self.verifier.verify_response(text_wrong_format, self.sky_evidence)
        self.assertFalse(is_valid)
        self.assertTrue(any("FORMAT CONFUSION" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
