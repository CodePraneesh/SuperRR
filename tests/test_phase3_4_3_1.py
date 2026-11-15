#!/usr/bin/env python3
"""
test_phase3_4_3_1.py
Unit test suite for Phase 3.4.3.1 Corrective Verification deliverables.
"""
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3_4_3_1'

class TestPhase3431(unittest.TestCase):

    def test_01_deliverable_files_exist_and_populated(self):
        """Test that all 6 required deliverable files exist and have non-zero size."""
        required_files = [
            'convergence_reconciliation.csv',
            'factorial_decomposition_correction.csv',
            'jensen_inequality_verification.md',
            'cluster_identifier_validation.md',
            'uncertainty_reporting_validation.md',
            'phase3_4_3_1_corrective_report.md'
        ]
        for fname in required_files:
            fpath = OUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Deliverable {fname} does not exist.")
            self.assertGreater(fpath.stat().st_size, 100, f"Deliverable {fname} is too small / empty.")

    def test_02_reconciled_1000_iteration_results(self):
        """Verify reconciliation of 1,000-iteration results across Task 2 and Task 4."""
        rec_df = pd.read_csv(OUT_DIR / 'convergence_reconciliation.csv')
        self.assertEqual(len(rec_df), 4)
        
        target_names = set(rec_df['player_name'])
        expected_names = {'Rinku Singh', 'Matthew Wade', 'Matheesha Pathirana', 'Sufiyan Muqeem'}
        self.assertEqual(target_names, expected_names)

        # Check that discrepancies are small (< 1.5% probability, < 1.0 point CPRI)
        for _, row in rec_df.iterrows():
            self.assertLessEqual(abs(row['discrepancy_rank1_pct']), 1.5)
            self.assertLessEqual(abs(row['discrepancy_top10_pct']), 1.5)
            self.assertLessEqual(abs(row['discrepancy_mean_cpri']), 1.0)
            self.assertTrue(len(str(row['reconciliation_root_cause'])) > 20)

    def test_03_convergence_correction_bounds(self):
        """Verify that convergence audit correctly identified boundary violations."""
        conv_df = pd.read_csv(BASE_DIR / 'output' / 'phase3_4_3' / 'bootstrap_convergence.csv')
        
        # Matthew Wade rank 1 delta between 1000 and 2500 is 1.80% (violates +-0.4% claim)
        wade_1k = conv_df[(conv_df['player_name'] == 'Matthew Wade') & (conv_df['iterations_N'] == 1000)].iloc[0]
        wade_25k = conv_df[(conv_df['player_name'] == 'Matthew Wade') & (conv_df['iterations_N'] == 2500)].iloc[0]
        wade_r1_delta = abs(wade_25k['prob_rank_1_pct'] - wade_1k['prob_rank_1_pct'])
        self.assertGreater(wade_r1_delta, 1.0, "Wade Rank 1 delta should exceed 1.0%, disproving +-0.4% claim.")

        # Sufiyan Muqeem mean CPRI delta between 1000 and 2500 is 0.29 (violates < 0.09 claim)
        muqeem_1k = conv_df[(conv_df['player_name'] == 'Sufiyan Muqeem') & (conv_df['iterations_N'] == 1000)].iloc[0]
        muqeem_25k = conv_df[(conv_df['player_name'] == 'Sufiyan Muqeem') & (conv_df['iterations_N'] == 2500)].iloc[0]
        muqeem_mean_delta = abs(muqeem_25k['conditional_cpri_mean'] - muqeem_1k['conditional_cpri_mean'])
        self.assertGreater(muqeem_mean_delta, 0.20, "Muqeem mean CPRI delta should exceed 0.20 points, disproving <0.09 claim.")

    def test_04_factorial_decomposition_metrics(self):
        """Verify that 2x2 factorial decomposition metrics are calculated accurately."""
        fact_df = pd.read_csv(OUT_DIR / 'factorial_decomposition_correction.csv').set_index('player_name')
        self.assertEqual(len(fact_df), 6)

        # Rinku Singh reduction should be ~75.78% (not > 80%)
        rinku_red = fact_df.loc['Rinku Singh', 'pct_drop_reduction_fixed_norm']
        self.assertAlmostEqual(rinku_red, 75.78, delta=0.5)
        self.assertLess(rinku_red, 80.0, "Rinku drop reduction must not exceed 80%.")

        # Ashutosh Sharma reduction should be ~49.52%
        ashu_red = fact_df.loc['Ashutosh Sharma', 'pct_drop_reduction_fixed_norm']
        self.assertAlmostEqual(ashu_red, 49.52, delta=0.5)

        # Verify that fixed norm deltas remain strictly negative for high-variance players
        self.assertLess(fact_df.loc['Rinku Singh', 'cond2_fixed_norm_delta'], 0.0)
        self.assertLess(fact_df.loc['Ashutosh Sharma', 'cond2_fixed_norm_delta'], 0.0)
        self.assertLess(fact_df.loc['Matheesha Pathirana', 'cond2_fixed_norm_delta'], 0.0)
        self.assertLess(fact_df.loc['Sufiyan Muqeem', 'cond2_fixed_norm_delta'], 0.0)

    def test_05_jensen_inequality_inflection_and_shift(self):
        """Verify that Jensen's inequality document records inflection crossing and shifts."""
        jensen_path = OUT_DIR / 'jensen_inequality_verification.md'
        content = jensen_path.read_text(encoding='utf-8')

        self.assertIn("S''(0) = 0", content)
        self.assertIn("Strictly Concave", content)
        self.assertIn("Strictly Convex", content)
        self.assertIn("-0.762", content)  # Rinku CPRI impact
        self.assertIn("-1.399", content)  # Muqeem CPRI impact
        self.assertIn("withdraw the blanket claim", content)

    def test_06_cluster_identifiers_structure(self):
        """Verify cluster identifier validation reports 131 T20I and 5 IPL clusters."""
        cluster_path = OUT_DIR / 'cluster_identifier_validation.md'
        content = cluster_path.read_text(encoding='utf-8')

        self.assertIn("131 clusters", content)
        self.assertIn("5 clusters", content)
        self.assertIn("32.8", content)

    def test_07_uncertainty_reporting_probability_ordering(self):
        """Verify strict probability ordering P(Rank=1) <= P(Top 10) <= P(Eligible)."""
        unc_df = pd.read_csv(BASE_DIR / 'output' / 'phase3_4_3' / 'conditional_unconditional_uncertainty.csv')
        
        # Check all 704 records
        for _, row in unc_df.iterrows():
            p_r1 = row['prob_rank_1_pct']
            p_t10 = row['prob_top10_pct']
            p_elig = row['prob_eligibility_pct']
            self.assertLessEqual(p_r1, p_t10 + 1e-5, f"P(R1) {p_r1} > P(T10) {p_t10} for {row['player_name']}")
            self.assertLessEqual(p_t10, p_elig + 1e-5, f"P(T10) {p_t10} > P(Elig) {p_elig} for {row['player_name']}")

    def test_08_final_report_verdict_and_matrix(self):
        """Verify final corrective report structure, verdict, and resolution matrix."""
        rep_path = OUT_DIR / 'phase3_4_3_1_corrective_report.md'
        content = rep_path.read_text(encoding='utf-8')

        self.assertIn("APPROVED WITH LIMITATIONS", content)
        self.assertIn("Issue Reconciliation Matrix", content)
        self.assertIn("Resolved", content)
        self.assertIn("Resolved with limitations", content)

if __name__ == '__main__':
    unittest.main()
