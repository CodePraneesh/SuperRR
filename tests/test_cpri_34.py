#!/usr/bin/env python3
"""
tests/test_cpri_34.py
Unit tests for Phase 3.4: Statistical Stress Testing & Validation.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_4'

class TestCPRI34(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.4 deliverables for test validation...")
        cls.wade_audit = pd.read_csv(OUTPUT_DIR / 'matthew_wade_match_audit.csv')
        cls.sig_sens = pd.read_csv(OUTPUT_DIR / 'sigmoid_sensitivity.csv')
        cls.weight_sens = pd.read_csv(OUTPUT_DIR / 'weight_sensitivity.csv')
        cls.elig_sens = pd.read_csv(OUTPUT_DIR / 'eligibility_sensitivity.csv')
        cls.boot_ci = pd.read_csv(OUTPUT_DIR / 'bootstrap_confidence_intervals.csv')
        print("Loaded Phase 3.4 datasets.")

    def test_01_all_7_deliverables_exist_and_populated(self):
        """Test that all 7 required Phase 3.4 deliverables exist and are non-empty."""
        expected_files = [
            'reliability_formula_audit.md',
            'matthew_wade_match_audit.csv',
            'sigmoid_sensitivity.csv',
            'weight_sensitivity.csv',
            'eligibility_sensitivity.csv',
            'bootstrap_confidence_intervals.csv',
            'final_statistical_validation_report.md'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_matthew_wade_match_audit_integrity(self):
        """Verify delivery and match audit facts for Matthew Wade in T20I."""
        self.assertEqual(len(self.wade_audit), 12, "Matthew Wade must have exactly 12 pressure matches in T20I!")
        self.assertTrue(self.wade_audit['positive_match'].all(), "All 12 matches for Wade must be positive (100% positive match ratio)!")
        self.assertEqual(int(self.wade_audit['actual_dismissals'].sum()), 2, "Wade must have exactly 2 dismissals across pressure deliveries!")
        self.assertEqual(int(self.wade_audit['actual_runs'].sum()), 281, "Wade must have 281 actual runs across pressure deliveries!")
        self.assertEqual(int(self.wade_audit['pressure_deliveries'].sum()), 160, "Wade must have 160 pressure deliveries in T20I!")
        self.assertGreaterEqual(float(self.wade_audit['wilson_95_ci_lower'].iloc[0]), 0.75, "Wilson 95% lower bound must exceed 75%!")

    def test_03_sigmoid_sensitivity_bounds_and_correlations(self):
        """Test that sigmoid sensitivity tested all k values and shows high Spearman correlation."""
        expected_k = {0.3, 0.45, 0.6, 0.75, 0.9, 1.2}
        tested_k = set(self.sig_sens['slope_k'].unique())
        self.assertTrue(expected_k.issubset(tested_k), "All 6 required slope k values must be tested!")
        self.assertTrue((self.sig_sens['spearman_correlation_with_baseline'] >= 0.98).all(), "Spearman correlation with baseline must exceed 0.98 across all configs!")

    def test_04_weight_sensitivity_and_champion_stability(self):
        """Verify that all weight configurations sum to 1.0 and champions remain predominantly stable."""
        weights_sum = (
            self.weight_sens['w_pressure_impact'] +
            self.weight_sens['w_adaptability'] +
            self.weight_sens['w_consistency'] +
            self.weight_sens['w_reliability']
        ).round(2)
        self.assertTrue((weights_sum == 1.0).all(), "All tested weight configurations must sum to 100%!")
        # Across 20 scenarios, champion stability must be >= 90%
        stability_rate = self.weight_sens['champion_stable'].mean()
        self.assertGreaterEqual(stability_rate, 0.90, "Champion stability rate must be >= 90% across weight configurations!")

    def test_05_bootstrap_confidence_intervals_validity(self):
        """Verify that bootstrap confidence intervals contain the baseline score and show low standard error."""
        self.assertTrue((self.boot_ci['bootstrap_ci_95_lower'] <= self.boot_ci['bootstrap_ci_95_upper']).all())
        # Baseline score must be contained in the 95% interval
        in_interval = (
            (self.boot_ci['baseline_cpri_score'] >= self.boot_ci['bootstrap_ci_95_lower'] - 0.1) &
            (self.boot_ci['baseline_cpri_score'] <= self.boot_ci['bootstrap_ci_95_upper'] + 0.1)
        )
        self.assertTrue(in_interval.all(), "All baseline CPRI scores must lie within the 95% bootstrap interval!")

if __name__ == '__main__':
    unittest.main()
