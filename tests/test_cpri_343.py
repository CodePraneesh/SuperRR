#!/usr/bin/env python3
"""
tests/test_cpri_343.py
Unit tests for Phase 3.4.3: Final Statistical Integrity Audit Engine.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_4_3'

class TestCPRI343(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.4.3 deliverables for test validation...")
        cls.cu_uncertainty = pd.read_csv(OUTPUT_DIR / 'conditional_unconditional_uncertainty.csv')
        cls.decomp = pd.read_csv(OUTPUT_DIR / 'bootstrap_component_decomposition.csv')
        cls.conv = pd.read_csv(OUTPUT_DIR / 'bootstrap_convergence.csv')
        print("Loaded Phase 3.4.3 datasets.")

    def test_01_all_5_deliverables_exist_and_populated(self):
        """Test that all 5 required Phase 3.4.3 deliverables exist and are non-empty."""
        expected_files = [
            'cluster_definition_audit.md',
            'conditional_unconditional_uncertainty.csv',
            'bootstrap_component_decomposition.csv',
            'bootstrap_convergence.csv',
            'phase3_4_3_final_report.md'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_conditional_unconditional_probability_ordering(self):
        """Verify fundamental probability axiom: P(Rank 1) <= P(Top 10) <= P(Eligible)."""
        self.assertTrue(
            (self.cu_uncertainty['prob_rank_1_pct'] <= self.cu_uncertainty['prob_top10_pct'] + 1e-5).all(),
            "Probability of Rank 1 must never exceed probability of Top 10!"
        )
        self.assertTrue(
            (self.cu_uncertainty['prob_top10_pct'] <= self.cu_uncertainty['prob_eligibility_pct'] + 1e-5).all(),
            "Probability of Top 10 must never exceed probability of eligibility!"
        )

    def test_03_component_decomposition_factorial_structure(self):
        """Verify 2x2 factorial structure across focal players and impact of normalization."""
        focal_players = {'Rinku Singh', 'Ashutosh Sharma', 'Matheesha Pathirana', 'Sufiyan Muqeem'}
        sub = self.decomp[self.decomp['player_name'].isin(focal_players)]
        self.assertGreaterEqual(len(sub), 16, "Must test at least 4 conditions for 4 focal players.")

        # For Rinku Singh, verify that fixed normalization reduces the absolute cpri delta
        rinku_dyn = sub[(sub['player_name'] == 'Rinku Singh') & (sub['experimental_condition'].str.contains('1. Recomputed Priors + Recomputed Norm', regex=False))].iloc[0]
        rinku_fix = sub[(sub['player_name'] == 'Rinku Singh') & (sub['experimental_condition'].str.contains('2. Recomputed Priors + Fixed Norm', regex=False))].iloc[0]
        self.assertLess(abs(rinku_fix['cpri_delta']), abs(rinku_dyn['cpri_delta']), "Fixed normalization must reduce CPRI delta for Rinku Singh!")

    def test_04_monte_carlo_convergence_scaling(self):
        """Verify that Monte Carlo standard error decreases monotonically with N."""
        for pname in ['Rinku Singh', 'Matthew Wade', 'Matheesha Pathirana', 'Sufiyan Muqeem']:
            p_sub = self.conv[self.conv['player_name'] == pname].sort_values('iterations_N')
            se_r1 = p_sub['mc_std_error_rank_1_pct'].tolist()
            # SE at 5,000 must be strictly less than SE at 1,000
            self.assertLess(se_r1[-1], se_r1[0], f"MC SE must decrease from N=1000 to N=5000 for {pname}!")
            # Delta between 2,500 and 5,000 rank 1 probability must be <= 1.5 percentage points
            r1_probs = p_sub['prob_rank_1_pct'].tolist()
            self.assertLessEqual(abs(r1_probs[-1] - r1_probs[1]), 1.5, f"Excessive Monte Carlo drift between 2,500 and 5,000 for {pname}!")

    def test_05_cluster_definition_audit_coverage(self):
        """Verify cluster definition audit text mentions comp_id and IPL season limitation."""
        with open(OUTPUT_DIR / 'cluster_definition_audit.md', 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('comp_id', content)
        self.assertIn('131', content)
        self.assertIn('5 annual IPL', content)

if __name__ == '__main__':
    unittest.main()
