#!/usr/bin/env python3
"""
tests/test_cpri_342.py
Unit tests for Phase 3.4.2: Bootstrap Consistency Audit & Verification Engine.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_4_2'

class TestCPRI342(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.4.2 deliverables for test validation...")
        cls.rank_dist = pd.read_csv(OUTPUT_DIR / 'bootstrap_rank_distribution.csv')
        cls.champ_rep = pd.read_csv(OUTPUT_DIR / 'champion_probability_report.csv')
        cls.se_comp = pd.read_csv(OUTPUT_DIR / 'bootstrap_se_comparison.csv')
        cls.mean_disc = pd.read_csv(OUTPUT_DIR / 'bootstrap_mean_discrepancy_audit.csv')
        print("Loaded Phase 3.4.2 datasets.")

    def test_01_all_6_deliverables_exist_and_populated(self):
        """Test that all 6 required Phase 3.4.2 deliverables exist and are non-empty."""
        expected_files = [
            'bootstrap_rank_distribution.csv',
            'champion_probability_report.csv',
            'bootstrap_se_comparison.csv',
            'bootstrap_mean_discrepancy_audit.csv',
            'bootstrap_implementation_audit.md',
            'phase3_4_2_final_report.md'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_rank_probability_and_interval_mathematical_consistency(self):
        """Verify mathematical consistency of rank probabilities and percentile bounds."""
        # Axiom: P(Rank 1) <= P(Top 10) <= P(Eligible)
        self.assertTrue(
            (self.rank_dist['prob_rank_1_pct'] <= self.rank_dist['prob_top10_pct'] + 1e-5).all(),
            "Probability of Rank 1 must never exceed probability of Top 10!"
        )
        self.assertTrue(
            (self.rank_dist['prob_top10_pct'] <= self.rank_dist['qualification_rate_pct'] + 1e-5).all(),
            "Probability of Top 10 must never exceed qualification rate!"
        )

        # Conditional rank interval ordering
        qual_mask = self.rank_dist['qualification_rate_pct'] > 0
        sub = self.rank_dist[qual_mask]
        for _, row in sub.iterrows():
            interval_str = row['conditional_rank_95_interval']
            low, high = map(int, interval_str.strip('[]').split(','))
            self.assertLessEqual(low, high, f"Inverted interval for {row['player_name']}: [{low}, {high}]")

    def test_03_champion_report_four_pillars_separation(self):
        """Verify champion report cleanly isolates concepts A, B, C, and D across all 4 cohorts."""
        self.assertEqual(len(self.champ_rep), 4, "Must contain exactly 4 cohort rows.")
        expected_champs = {
            'IPL Batters': 'Rinku Singh',
            'T20I Batters': 'Matthew Wade',
            'IPL Bowlers': 'Matheesha Pathirana',
            'T20I Bowlers': 'Sufiyan Muqeem'
        }
        for _, row in self.champ_rep.iterrows():
            cohort = row['cohort']
            self.assertEqual(row['concept_A_point_estimate_champion'], expected_champs[cohort])
            # Rank 1 prob must be <= 100% and >= 0%
            self.assertGreaterEqual(row['concept_D_match_bootstrap_rank1_prob'], 0.0)
            self.assertLessEqual(row['concept_D_match_bootstrap_rank1_prob'], 100.0)

    def test_04_bootstrap_se_comparison_validity(self):
        """Verify that standard error comparisons are populated and contain valid numbers."""
        self.assertGreater(len(self.se_comp), 250, "Must contain comparisons for all qualified cohort players.")
        self.assertTrue((self.se_comp['match_bootstrap_se'] > 0).all())
        self.assertTrue((self.se_comp['tournament_bootstrap_se'] > 0).all())
        # Matthew Wade SE increase check
        wade_row = self.se_comp[self.se_comp['player_name'] == 'Matthew Wade'].iloc[0]
        self.assertTrue(wade_row['se_increased_under_tournament'], "Matthew Wade tournament SE must be greater than match SE under 49-series clustering!")

    def test_05_mean_discrepancy_audit_bounds(self):
        """Verify that all audited mean discrepancies fall within legitimate sampling error bounds (2 SE)."""
        self.assertGreaterEqual(len(self.mean_disc), 9, "Must audit key players from all 4 cohorts.")
        self.assertTrue(
            self.mean_disc['within_2_se_bound'].all(),
            "All mean discrepancies must fall within 2 standard errors of the estimate!"
        )

if __name__ == '__main__':
    unittest.main()
