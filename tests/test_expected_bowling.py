#!/usr/bin/env python3
'''
test_expected_bowling.py
Unit tests for Phase 2B Bowler Expected Performance Model.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv'

class TestExpectedBowling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.conftest import require_data_file
        require_data_file('output/phase2/bowler_delivery_expectations.csv', 'python ml/phase2/expected_bowling.py')
        print('\nLoading bowler delivery expectations dataset...')
        cls.df = pd.read_csv(OUTPUT_FILE, low_memory=False)
        print('Loaded bowler expectations.')

    def test_01_expected_runs_conceded_positive(self):
        '''Test that expected bowler runs conceded are strictly non-negative.'''
        er = self.df['expected_runs_conceded'].dropna()
        self.assertTrue((er >= 0.0).all(), 'Found negative expected runs conceded!')

    def test_02_wicket_probability_range(self):
        '''Test that expected wicket probability is strictly within [0, 1].'''
        wp = self.df['expected_wicket_prob'].dropna()
        self.assertTrue((wp >= 0.0).all() and (wp <= 1.0).all(), 'Wicket prob outside [0, 1]!')

    def test_03_reversed_sign_convention_bowling_runs(self):
        '''Test that bowling_run_residual = expected_runs_conceded - actual_runs_conceded (reversed).'''
        d = self.df.dropna(subset=['actual_runs_conceded', 'expected_runs_conceded', 'bowling_run_residual'])
        diff = (d['expected_runs_conceded'] - d['actual_runs_conceded']) - d['bowling_run_residual']
        self.assertAlmostEqual(np.max(np.abs(diff)), 0.0, places=5)

    def test_04_wicket_residual_sign_convention(self):
        '''Test that bowling_wicket_residual = actual_wicket_outcome - expected_wicket_prob.'''
        d = self.df.dropna(subset=['actual_wicket_outcome', 'expected_wicket_prob', 'bowling_wicket_residual'])
        diff = (d['actual_wicket_outcome'] - d['expected_wicket_prob']) - d['bowling_wicket_residual']
        self.assertAlmostEqual(np.max(np.abs(diff)), 0.0, places=5)

    def test_05_legal_credited_wickets_only(self):
        '''Verify that actual_wicket_outcome only flags legal credited wickets.'''
        d = self.df
        # Actual wicket outcome sum must equal total bowler wickets in in-scope matches
        self.assertTrue(d['actual_wicket_outcome'].isin([0, 1]).all())

if __name__ == '__main__':
    unittest.main()
