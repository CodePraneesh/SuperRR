#!/usr/bin/env python3
'''
test_performance_delta.py
Unit tests for Phase 2B Performance Delta, Pressure Weighting, and Player Aggregations.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
BAT_SUM_FILE = BASE_DIR / 'output' / 'phase2' / 'batter_performance_summary.csv'
BOWL_SUM_FILE = BASE_DIR / 'output' / 'phase2' / 'bowler_performance_summary.csv'

class TestPerformanceDelta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.conftest import require_data_file
        require_data_file('output/phase2/batter_performance_summary.csv', 'python ml/phase2/performance_delta.py')
        require_data_file('output/phase2/bowler_performance_summary.csv', 'python ml/phase2/performance_delta.py')
        print('\nLoading player performance summary datasets...')
        cls.batters = pd.read_csv(BAT_SUM_FILE, low_memory=False)
        cls.bowlers = pd.read_csv(BOWL_SUM_FILE, low_memory=False)
        print('Loaded player performance summaries.')

    def test_01_ipl_and_t20i_separated(self):
        '''Test that summaries strictly separate IPL and T20I.'''
        bat_scopes = set(self.batters['competition_scope'].unique())
        bowl_scopes = set(self.bowlers['competition_scope'].unique())
        self.assertEqual(bat_scopes, {'IPL', 'T20I'})
        self.assertEqual(bowl_scopes, {'IPL', 'T20I'})

    def test_02_bayesian_shrinkage_direction(self):
        '''Test that shrunk residual is smaller in magnitude than raw residual (pulled to 0).'''
        # For non-zero residuals, abs(shrunk) <= abs(raw)
        b = self.batters[self.batters['total_deliveries_faced'] >= 10].copy()
        diff = np.abs(b['shrunk_run_residual']) - np.abs(b['raw_run_residual'])
        self.assertTrue((diff <= 0.05).all(), 'Shrinkage must pull residuals towards zero!')

    def test_03_no_player_hidden_confidence_tiers(self):
        '''Verify that small-sample players are not hidden but tagged with low confidence tier.'''
        tiers = set(self.batters['confidence_tier'].unique())
        self.assertIn('Low Confidence (Small Sample)', tiers)
        self.assertIn('High Confidence', tiers)
        small_sample_players = self.batters[self.batters['total_deliveries_faced'] < 60]
        self.assertTrue((small_sample_players['confidence_tier'] == 'Low Confidence (Small Sample)').all())

    def test_04_pressure_and_nonpressure_split_consistency(self):
        '''Test that total_deliveries = pressure_deliveries + nonpressure_deliveries.'''
        b = self.batters
        ball_diff = (b['pressure_deliveries'] + b['nonpressure_deliveries']) - b['total_deliveries_faced']
        self.assertEqual(np.abs(ball_diff).sum(), 0)

    def test_05_bowler_credited_wickets_non_negative(self):
        '''Test that actual credited wickets are non-negative and properly tracked.'''
        bw = self.bowlers
        self.assertTrue((bw['actual_credited_wickets'] >= 0).all())
        self.assertTrue((bw['expected_wickets'] >= 0.0).all())

if __name__ == '__main__':
    unittest.main()
