#!/usr/bin/env python3
'''
test_win_probability.py
Unit tests for Phase 2C Win Probability Models.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'win_probability_predictions.csv'

class TestWinProbability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nLoading win probability predictions dataset...')
        cls.df = pd.read_csv(OUTPUT_FILE, low_memory=False)
        print('Loaded win probability dataset.')

    def test_01_probabilities_bounded_between_0_and_1(self):
        '''Test that all predicted probabilities fall strictly in [0, 1].'''
        p_before = self.df['p_win_before'].dropna()
        p_after = self.df['p_win_after'].dropna()
        
        self.assertTrue((p_before >= 0.0).all() and (p_before <= 1.0).all(), 'p_win_before out of [0, 1]!')
        self.assertTrue((p_after >= 0.0).all() and (p_after <= 1.0).all(), 'p_win_after out of [0, 1]!')

    def test_02_terminal_target_reached_gives_one(self):
        '''Test that chasing deliveries reaching or exceeding target achieve p_win_after == 1.0.'''
        chase = self.df[self.df['innings'] == 2]
        # When score_before + runs >= target_runs
        target_met = chase[chase['runs_required'] <= 0.0]
        if len(target_met) > 0:
            self.assertTrue((target_met['p_win_before'] == 1.0).all())

    def test_03_chase_monotonic_with_required_run_rate(self):
        '''Test that win probability decreases as required run rate increases in chase.'''
        chase = self.df[(self.df['innings'] == 2) & (self.df['balls_remaining'] > 12)]
        low_rrr_win = chase[chase['required_run_rate'] <= 6.0]['p_win_before'].median()
        high_rrr_win = chase[chase['required_run_rate'] >= 13.0]['p_win_before'].median()
        self.assertGreater(low_rrr_win, high_rrr_win, 'Low RRR should have higher win prob than High RRR!')

    def test_04_wickets_in_hand_impact(self):
        '''Test that having more wickets in hand increases batting team win probability.'''
        chase = self.df[(self.df['innings'] == 2) & (self.df['required_run_rate'].between(8.0, 10.0))]
        top_order = chase[chase['wickets_lost_before'] <= 2]['p_win_before'].median()
        tail = chase[chase['wickets_lost_before'] >= 7]['p_win_before'].median()
        self.assertGreater(top_order, tail, 'More wickets in hand must improve win probability!')

if __name__ == '__main__':
    unittest.main()
