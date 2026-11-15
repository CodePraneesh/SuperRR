#!/usr/bin/env python3
'''
test_wpa_attribution.py
Unit tests for Phase 2C WPA Attribution Rules.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv'
SUMMARY_FILE = BASE_DIR / 'output' / 'phase2' / 'player_wpa_summary.csv'

class TestWPAAttribution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nLoading delivery WPA and player summary datasets...')
        cls.df = pd.read_csv(OUTPUT_FILE, low_memory=False)
        cls.summary = pd.read_csv(SUMMARY_FILE, low_memory=False)
        print('Loaded attribution datasets.')

    def test_01_byes_legbyes_unattributed_to_bowler_or_batter(self):
        '''Test that pure byes and leg-byes are assigned to unattributed_wpa, not batter or bowler.'''
        extras_df = self.df[self.df['extras_label'].isin(['byes', 'legbyes'])]
        if len(extras_df) > 0:
            self.assertTrue((extras_df['batting_wpa'] == 0.0).all(), 'Byes/legbyes must not credit batting WPA!')
            self.assertTrue((extras_df['bowling_wpa'] == 0.0).all(), 'Byes/legbyes must not credit bowling WPA!')

    def test_02_ambiguous_extras_isolated(self):
        '''Test that ambiguous extras are completely marked as unattributed.'''
        # In delivery_wpa, ambiguous extras rows have batting_wpa == 0 and bowling_wpa == 0
        ambig = self.df[self.df['extras_label'].isin(['other', 'penalty'])]
        if len(ambig) > 0:
            self.assertTrue((ambig['batting_wpa'] == 0.0).all(), 'Ambiguous extras must not assign batting WPA!')
            self.assertTrue((ambig['bowling_wpa'] == 0.0).all(), 'Ambiguous extras must not assign bowling WPA!')

    def test_03_bowler_wicket_positive_for_bowler(self):
        '''Test that legitimate bowler wickets yield positive bowling WPA (helped bowling team).'''
        # In second innings, a bowler wicket lowers batting team win prob (delivery_wpa < 0).
        # bowling_wpa should be positive.
        bw_chase = self.df[(self.df['innings'] == 2) & (self.df['bowler_wicket'] == True)]
        if len(bw_chase) > 0:
            self.assertTrue((bw_chase['bowling_wpa'] >= 0.0).all(), 'Bowler wickets must yield non-negative bowling WPA!')

    def test_04_player_summary_roles_separated(self):
        '''Test that player summary cleanly distinguishes Batter and Bowler roles and scopes.'''
        roles = set(self.summary['role'].unique())
        self.assertEqual(roles, {'Batter', 'Bowler'})
        scopes = set(self.summary['competition_scope'].unique())
        self.assertEqual(scopes, {'IPL', 'T20I'})

    def test_05_confidence_tiers_assigned_transparently(self):
        '''Test that confidence tiers are populated without dropping small sample players.'''
        tiers = set(self.summary['confidence_tier'].unique())
        self.assertIn('High Confidence', tiers)
        self.assertIn('Low Confidence', tiers)

if __name__ == '__main__':
    unittest.main()
