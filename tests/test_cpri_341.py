#!/usr/bin/env python3
"""
tests/test_cpri_341.py
Unit tests for Phase 3.4.1: Corrective Statistical Audit & Reproduction Engine.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_4_1'

class TestCPRI341(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.4.1 deliverables for test validation...")
        cls.weights = pd.read_csv(OUTPUT_DIR / 'weight_validation.csv')
        cls.sig_complete = pd.read_csv(OUTPUT_DIR / 'sigmoid_sensitivity_complete.csv')
        cls.elig_complete = pd.read_csv(OUTPUT_DIR / 'eligibility_sensitivity_complete.csv')
        cls.ranking_reprod = pd.read_csv(OUTPUT_DIR / 'ranking_reproduction_audit.csv')
        print("Loaded Phase 3.4.1 datasets.")

    def test_01_all_7_deliverables_exist_and_populated(self):
        """Test that all 7 required Phase 3.4.1 deliverables exist and are non-empty."""
        expected_files = [
            'reliability_audit.md',
            'weight_validation.csv',
            'sigmoid_sensitivity_complete.csv',
            'bootstrap_methodology_audit.md',
            'eligibility_sensitivity_complete.csv',
            'ranking_reproduction_audit.csv',
            'phase3_4_1_final_report.md'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_weight_validation_and_sums(self):
        """Verify weight validation matrix contains both raw and normalized variants and tests sums."""
        self.assertGreaterEqual(len(self.weights), 20, "Must test at least 20 weight scenarios across cohorts.")
        # Check normalized and adjusted configurations sum to 1.0
        valid_sums = self.weights[self.weights['configuration_name'].str.contains('Normalized|Adjusted|Baseline|heavy')]
        normalized_subset = valid_sums[~valid_sums['configuration_name'].str.contains('Raw')]
        self.assertTrue((normalized_subset['sums_to_100_pct']).all(), "All normalized/adjusted weight configurations must sum to 100%!")

    def test_03_sigmoid_sensitivity_72_combinations(self):
        """Verify that sigmoid sensitivity matrix covers exactly 72 combinations (4 cohorts x 6 slopes x 3 estimators)."""
        self.assertEqual(len(self.sig_complete), 72, f"Expected exactly 72 rows, got {len(self.sig_complete)}")
        expected_estimators = {'IQR/1.349', 'MAD/0.6745', 'Winsorized Std'}
        tested_estimators = set(self.sig_complete['scale_estimator'].unique())
        self.assertEqual(expected_estimators, tested_estimators, "Must test exactly the 3 required scale estimators!")
        expected_slopes = {0.3, 0.45, 0.6, 0.75, 0.9, 1.2}
        tested_slopes = set(self.sig_complete['slope_k'].unique())
        self.assertEqual(expected_slopes, tested_slopes, "Must test all 6 required slope values!")
        self.assertTrue((self.sig_complete['spearman_correlation_with_baseline'] >= 0.98).all())

    def test_04_eligibility_sensitivity_100_combinations(self):
        """Verify that eligibility grid covers 100 combinations (4 cohorts x 25 grid cells) with baseline constraints."""
        self.assertEqual(len(self.elig_complete), 100, f"Expected exactly 100 rows, got {len(self.elig_complete)}")
        # Check that baseline delivery filters are explicit
        batters_subset = self.elig_complete[self.elig_complete['role'] == 'Batter']
        self.assertTrue((batters_subset['baseline_filter_deliveries'] == 150).all())
        bowlers_subset = self.elig_complete[self.elig_complete['role'] == 'Bowler']
        self.assertTrue((bowlers_subset['baseline_filter_deliveries'] == 180).all())

    def test_05_ranking_reproduction_audit_consistency(self):
        """Verify that official rankings reproduction contains 40 entries and Matthew Wade remains champion."""
        self.assertEqual(len(self.ranking_reprod), 40, "Must contain exactly 40 entries for the 4 official Top 10 cohorts.")
        wade_entry = self.ranking_reprod[(self.ranking_reprod['player_name'] == 'Matthew Wade') & (self.ranking_reprod['competition_scope'] == 'T20I')]
        self.assertEqual(len(wade_entry), 1, "Matthew Wade must be present in T20I Top 10.")
        self.assertEqual(wade_entry['official_rank'].iloc[0], 1, "Matthew Wade must be official Rank 1.")
        self.assertAlmostEqual(wade_entry['official_cpri_score'].iloc[0], 97.42, delta=0.05)

if __name__ == '__main__':
    unittest.main()
