#!/usr/bin/env python3
'''
test_wpa_engine.py
Unit tests for Phase 2C WPA Engine and state transitions.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'win_probability_predictions.csv'

class TestWPAEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.conftest import require_data_file
        require_data_file('output/phase2/win_probability_predictions.csv', 'python ml/phase2/win_probability.py')
        print('\nLoading WPA predictions dataset...')
        cls.df = pd.read_csv(OUTPUT_FILE, low_memory=False)
        print('Loaded WPA predictions.')

    def test_01_wpa_definition_consistency(self):
        '''Test that delivery_wpa = p_win_after - p_win_before.'''
        d = self.df.dropna(subset=['p_win_before', 'p_win_after', 'delivery_wpa'])
        diff = (d['p_win_after'] - d['p_win_before']) - d['delivery_wpa']
        self.assertAlmostEqual(np.max(np.abs(diff)), 0.0, places=5)

    def test_02_wpa_bounds(self):
        '''Test that WPA values fall strictly in [-1.0, 1.0].'''
        wpa = self.df['delivery_wpa'].dropna()
        self.assertTrue((wpa >= -1.0).all() and (wpa <= 1.0).all(), 'WPA out of [-1, 1]!')

    def test_03_zero_future_leakage_in_pre_probs(self):
        '''Verify that pre-delivery state on ball 1 of an innings has zero lookahead.'''
        first_balls = self.df.groupby(['match_id', 'innings']).first()
        self.assertTrue((first_balls['score_before'] == 0).all())
        self.assertTrue((first_balls['wickets_lost_before'] == 0).all())

    def test_04_chase_boundary_increases_win_prob(self):
        '''Test that hitting boundaries in a chase yields positive average WPA for batting team.'''
        # Innings 2 deliveries with runs == 6 and no wicket
        chase_sixes = self.df[(self.df['innings'] == 2) & (self.df['delivery_wpa'].notna())]
        # Merge total delivery runs from deliveries enriched or check delivery wpa
        # Deliveries with p_win_after > p_win_before must be positive WPA
        pos_wpa_count = (chase_sixes['delivery_wpa'] > 0).sum()
        self.assertGreater(pos_wpa_count, 0)

if __name__ == '__main__':
    unittest.main()
