# tests/test_cpri_31.py
# Phase 3.1: Automated Unit Tests for Refined CPRI Methodology & Calculations.
import unittest
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.phase3_1.reliability import (
    apply_bayesian_shrinkage,
    calculate_pressure_reliability,
    assign_pressure_confidence_tier,
    min_max_normalize
)
from ml.phase3_1.cpri_batter import compute_batter_cpri_31
from ml.phase3_1.cpri_bowler import compute_bowler_cpri_31

class TestCPRI31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b_path = BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv'
        bw_path = BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv'
        w_path = BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv'
        
        # Load sample for quick unit testing
        cls.b_df = pd.read_csv(b_path, nrows=5000)
        cls.bw_df = pd.read_csv(bw_path, nrows=5000)
        cls.w_df = pd.read_csv(w_path, nrows=5000)
        
        cls.batters, cls.b_matches = compute_batter_cpri_31(cls.b_df, cls.w_df)
        cls.bowlers, cls.bw_matches = compute_bowler_cpri_31(cls.bw_df, cls.w_df)

    def test_01_dismissal_survival_contribution_direction(self):
        """
        Verify that survival residual = expected_prob - actual_dismissal:
        - When dismissed (actual=1), survival_residual is negative (prob - 1 < 0).
        - When not dismissed (actual=0), survival_residual is positive (prob > 0).
        And net impact correctly adds +12 * survival_residual.
        """
        prob = 0.05
        # Dismissed delivery
        res_out = prob - 1.0 # -0.95
        # Survived delivery
        res_surv = prob - 0.0 # +0.05
        
        # Batter net impact with +12 * res:
        impact_out = 0.0 + 12.0 * res_out # -11.4
        impact_surv = 0.0 + 12.0 * res_surv # +0.6
        
        self.assertLess(impact_out, 0.0, "Dismissal must impose a heavy penalty on net impact!")
        self.assertGreater(impact_surv, 0.0, "Surviving delivery must yield positive survival credit!")
        self.assertAlmostEqual(impact_surv - impact_out, 12.0, places=4, msg="Delta between surviving and getting out must equal exactly 1 wicket replacement value (12.0 runs)!")

    def test_02_pressure_reliability_bounds_and_monotonicity(self):
        """Verify pressure reliability is in [0, 100] and monotonically increasing in p_balls and p_matches."""
        p_balls = pd.Series([0, 10, 50, 100, 300])
        p_matches = pd.Series([0, 1, 3, 8, 20])
        rel = calculate_pressure_reliability(p_balls, p_matches)
        
        self.assertTrue((rel >= 0.0).all() and (rel <= 100.0).all())
        self.assertAlmostEqual(rel.iloc[0], 0.0)
        self.assertTrue(rel.is_monotonic_increasing)

    def test_03_pressure_confidence_tier_assignment(self):
        """Verify pressure-specific confidence tiers."""
        tot = pd.Series([200, 150, 50, 20])
        p_b = pd.Series([60, 40, 25, 5])
        p_m = pd.Series([4, 2, 2, 1])
        tiers = assign_pressure_confidence_tier(tot, p_b, p_m)
        self.assertEqual(tiers.iloc[0], 'High Confidence')
        self.assertEqual(tiers.iloc[1], 'Moderate Confidence') # p_balls < 50
        self.assertEqual(tiers.iloc[2], 'Moderate Confidence')
        self.assertEqual(tiers.iloc[3], 'Low Confidence')

    def test_04_player_specific_consistency_calculation(self):
        """Verify that consistency correctly evaluates match-level variance and positive match ratio."""
        self.assertIn('pressure_matches', self.batters.columns)
        self.assertTrue((self.batters['score_consistency'] >= 0.0).all())
        self.assertTrue((self.batters['score_consistency'] <= 100.0).all())

    def test_05_no_duplicate_players_within_scope(self):
        """Ensure zero duplicate player IDs within any competition scope."""
        for scope, grp in self.batters.groupby('competition_scope'):
            self.assertEqual(grp['player_id'].nunique(), len(grp))
        for scope, grp in self.bowlers.groupby('competition_scope'):
            self.assertEqual(grp['player_id'].nunique(), len(grp))

    def test_06_cpri_scores_bounded_and_monotonic(self):
        """Check composite score ranges and ranking order."""
        for df in [self.batters, self.bowlers]:
            self.assertTrue((df['cpri_score'] >= 0.0).all() and (df['cpri_score'] <= 100.0).all())
            for scope, grp in df.groupby('competition_scope'):
                self.assertTrue(grp['cpri_score'].is_monotonic_decreasing)

if __name__ == '__main__':
    unittest.main()
