#!/usr/bin/env python3
'''
test_expected_batting.py
Unit tests for Phase 2B Batter Expected Performance Model.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv'

class TestExpectedBatting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nLoading batter delivery expectations dataset...')
        cls.df = pd.read_csv(OUTPUT_FILE, low_memory=False)
        print('Loaded batter expectations.')

    def test_01_expected_runs_positive(self):
        '''Test that expected batter runs are strictly non-negative.'''
        er = self.df['expected_batter_runs'].dropna()
        self.assertTrue((er >= 0.0).all(), 'Found negative expected batter runs!')

    def test_02_dismissal_probability_range(self):
        '''Test that expected dismissal probability is strictly within [0, 1].'''
        ep = self.df['expected_dismissal_prob'].dropna()
        self.assertTrue((ep >= 0.0).all() and (ep <= 1.0).all(), 'Dismissal prob outside [0, 1]!')

    def test_03_residual_calculation(self):
        '''Test that batting_run_residual = actual_batter_runs - expected_batter_runs.'''
        d = self.df.dropna(subset=['actual_batter_runs', 'expected_batter_runs', 'batting_run_residual'])
        diff = (d['actual_batter_runs'] - d['expected_batter_runs']) - d['batting_run_residual']
        self.assertAlmostEqual(np.max(np.abs(diff)), 0.0, places=5)

    def test_04_pressure_impact_on_dismissal_risk(self):
        '''Test that high pressure situations exhibit significantly higher expected dismissal risk.'''
        d = self.df
        high_p_risk = d[d['pressure_score'] >= 75.0]['expected_dismissal_prob'].mean()
        low_p_risk = d[d['pressure_score'] <= 25.0]['expected_dismissal_prob'].mean()
        self.assertGreater(high_p_risk, low_p_risk, 'High pressure deliveries must carry higher dismissal risk!')

    def test_05_death_overs_higher_scoring_rate_than_powerplay(self):
        '''Test that death overs have a higher expected scoring rate than powerplay.'''
        d = self.df
        death_rate = d[d['innings_phase'] == 'death']['expected_batter_runs'].mean()
        pp_rate = d[d['innings_phase'] == 'powerplay']['expected_batter_runs'].mean()
        self.assertGreater(death_rate, pp_rate, 'Death overs should have higher expected scoring rate than powerplay!')

if __name__ == '__main__':
    unittest.main()
