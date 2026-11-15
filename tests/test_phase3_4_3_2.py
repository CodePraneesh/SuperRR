#!/usr/bin/env python3
"""
test_phase3_4_3_2.py
Unit test suite for Phase 3.4.3.2 Final Corrective Pass deliverables.
"""
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3_4_3_2'

class TestPhase3432(unittest.TestCase):

    def test_01_deliverable_files_exist_and_populated(self):
        """Test that all 6 Phase 3.4.3.2 deliverables exist and are populated."""
        required_files = [
            'sigmoid_derivative_validation.md',
            'factorial_recalculation.csv',
            'bootstrap_convergence_reconciliation.csv',
            'cluster_mapping_validation.csv',
            'test_coverage_and_limitations.md',
            'phase3_4_3_2_final_report.md'
        ]
        for fname in required_files:
            fpath = OUT_DIR / fname
            self.assertTrue(fpath.exists(), f"File {fname} does not exist.")
            self.assertGreater(fpath.stat().st_size, 100, f"File {fname} is too small / empty.")

    def test_02_sigmoid_mathematical_derivatives(self):
        """Verify symbolic and numerical first and second derivatives of S(z)."""
        def S(z):
            return 1.0 / (1.0 + np.exp(-0.6 * z))

        def S_prime(z):
            y = S(z)
            return 0.6 * y * (1.0 - y)

        def S_double_prime(z):
            y = S(z)
            return 0.36 * y * (1.0 - y) * (1.0 - 2.0 * y)

        # Inflection point check
        self.assertAlmostEqual(S_double_prime(0.0), 0.0, places=9)

        # Curvature signs
        self.assertGreater(S_double_prime(-1.5), 0.0, "S''(z) must be positive (convex) for z < 0")
        self.assertLess(S_double_prime(1.5), 0.0, "S''(z) must be negative (concave) for z > 0")

        # Numerical finite difference checks across grid
        h = 1e-5
        for z in [-2.5, -1.0, -0.2, 0.0, 0.2, 1.0, 2.5]:
            # First derivative numerical
            num_sp = (S(z + h) - S(z - h)) / (2 * h)
            ana_sp = S_prime(z)
            self.assertAlmostEqual(num_sp, ana_sp, places=5)

            # Second derivative numerical
            num_spp = (S(z + h) - 2 * S(z) + S(z - h)) / (h**2)
            ana_spp = S_double_prime(z)
            self.assertAlmostEqual(num_spp, ana_spp, places=4)

    def test_03_factorial_arithmetic_and_identities(self):
        """Verify 2x2 factorial arithmetic, exact ANOVA identity, and percentage denominators."""
        fact_df = pd.read_csv(OUT_DIR / 'factorial_recalculation.csv').set_index('player_name')
        self.assertEqual(len(fact_df), 6)

        for pname, row in fact_df.iterrows():
            # Exact identity check: Y11 - Y00 == alpha_A + alpha_B + alpha_AB
            y11 = row['cond1_recomp_priors_recomp_norm_Y11']
            y00 = row['cond4_fixed_priors_fixed_norm_Y00']
            total_shift = y11 - y00

            alpha_a = row['effect_norm_given_fixed_priors_alpha_A']
            alpha_b = row['effect_priors_given_fixed_norm_alpha_B']
            alpha_ab = row['interaction_effect_alpha_AB']
            identity_sum = alpha_a + alpha_b + alpha_ab

            self.assertAlmostEqual(total_shift, identity_sum, places=3, msg=f"Identity failed for {pname}")
            self.assertTrue(row['factorial_identity_verified'])

        # Rinku Singh reduction check
        rinku_red = fact_df.loc['Rinku Singh', 'pct_drop_reduction_holding_priors_recomputed']
        self.assertAlmostEqual(rinku_red, 75.78, delta=0.5)
        self.assertLess(rinku_red, 80.0, "Rinku drop reduction holding priors recomputed must be < 80%.")

    def test_04_probability_denominators_and_ordering(self):
        """Verify probability denominators and strict hierarchy P(R=1) <= P(Top 10) <= P(Eligible)."""
        conv_df = pd.read_csv(OUT_DIR / 'bootstrap_convergence_reconciliation.csv')
        self.assertGreaterEqual(len(conv_df), 12)

        for _, row in conv_df.iterrows():
            p_r1 = row['prob_rank_1_pct']
            p_t10 = row['prob_top10_pct']
            p_elig = row['prob_eligibility_pct']

            self.assertLessEqual(p_r1, p_t10 + 1e-4, f"P(R1) > P(T10) for {row['player_name']}")
            self.assertLessEqual(p_t10, p_elig + 1e-4, f"P(T10) > P(Elig) for {row['player_name']}")

    def test_05_cluster_mapping_and_ipl_five_seasons(self):
        """Verify cluster mapping validation contains 5 IPL seasons and 131 T20I series."""
        cmap_df = pd.read_csv(OUT_DIR / 'cluster_mapping_validation.csv')
        
        ipl_clusters = cmap_df[cmap_df['competition_scope'] == 'IPL']
        self.assertEqual(len(ipl_clusters), 5, "IPL must have exactly 5 annual season clusters.")
        for cnt in ipl_clusters['match_count']:
            self.assertIn(cnt, [74, 75], "Each IPL season must have 74 or 75 matches.")

        t20i_clusters = cmap_df[cmap_df['competition_scope'] == 'T20I']
        self.assertGreaterEqual(len(t20i_clusters), 130, "T20I must have at least 130 series clusters.")

    def test_06_final_report_verdict(self):
        """Verify final report decision is APPROVED WITH DOCUMENTED LIMITATIONS."""
        rep_path = OUT_DIR / 'phase3_4_3_2_final_report.md'
        content = rep_path.read_text(encoding='utf-8')
        self.assertIn("APPROVED WITH DOCUMENTED LIMITATIONS", content)
        self.assertNotIn("NOT APPROVED", content)

if __name__ == '__main__':
    unittest.main()
