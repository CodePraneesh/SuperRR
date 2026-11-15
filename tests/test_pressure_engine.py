#!/usr/bin/env python3
'''
test_pressure_engine.py
Automated unit tests for Phase 2A Dynamic Pressure Engine.
'''
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from ml.phase2.pressure_features import extract_predelivery_features
from ml.phase2.pressure_engine import DynamicPressureEngine

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / 'output' / 'phase2' / 'pressure_scored_deliveries.csv'
DIST_FILE = BASE_DIR / 'output' / 'phase2' / 'pressure_distribution.csv'

class TestPressureEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print('\nLoading Phase 2A pressure scored dataset...')
        cls.scored = pd.read_csv(OUTPUT_FILE, low_memory=False)
        cls.dist = pd.read_csv(DIST_FILE, low_memory=False)
        print('Pressure datasets loaded successfully.')

    def test_01_pressure_score_bounds(self):
        '''Test that all pressure scores fall strictly between 0 and 100.'''
        ps = self.scored['pressure_score'].dropna()
        self.assertTrue((ps >= 0.0).all(), 'Found negative pressure scores!')
        self.assertTrue((ps <= 100.0).all(), 'Found pressure scores exceeding 100!')

    def test_02_no_future_leakage_in_features(self):
        '''Verify that pre-delivery state features do not leak current ball runs or wickets.'''
        d = self.scored
        # On ball 1, score_before and wickets_lost_before must be exactly 0
        first_balls = d.groupby(['match_id', 'innings']).first()
        self.assertTrue((first_balls['score_before'] == 0).all(), 'score_before did not start at 0!')
        self.assertTrue((first_balls['wickets_lost_before'] == 0).all(), 'wickets_lost_before did not start at 0!')

    def test_03_first_and_second_innings_distinguishable(self):
        '''Test that 1st innings and chasing pressure scores are kept distinguishable.'''
        d = self.scored[self.scored['in_scope_competition'].fillna(False)]
        inn1 = d[d['innings'] == 1]
        inn2 = d[d['innings'] == 2]
        
        # 1st innings must have first_innings_pressure_score populated and chasing null
        self.assertTrue(inn1['first_innings_pressure_score'].notna().all())
        self.assertTrue(inn1['chasing_pressure_score'].isna().all())
        self.assertTrue(inn1['expected_remaining_runs'].notna().all())
        self.assertTrue(inn1['expected_final_total'].notna().all())
        
        # 2nd innings must have chasing_pressure_score populated and 1st innings null
        self.assertTrue(inn2['chasing_pressure_score'].notna().all())
        self.assertTrue(inn2['first_innings_pressure_score'].isna().all())
        self.assertTrue(inn2['expected_remaining_runs'].isna().all())

    def test_04_chase_monotonic_with_required_run_rate(self):
        '''Test that higher required run rate results in higher median pressure in chase.'''
        chase = self.scored[(self.scored['innings'] == 2) & (self.scored['in_scope_competition'].fillna(False))]
        low_rrr = chase[chase['required_run_rate'] < 6.0]['pressure_score'].median()
        med_rrr = chase[chase['required_run_rate'].between(7.0, 9.0)]['pressure_score'].median()
        high_rrr = chase[chase['required_run_rate'].between(11.0, 14.0)]['pressure_score'].median()
        extreme_rrr = chase[chase['required_run_rate'] > 15.0]['pressure_score'].median()
        
        self.assertLess(low_rrr, med_rrr)
        self.assertLess(med_rrr, high_rrr)
        self.assertLess(high_rrr, extreme_rrr)

    def test_05_wickets_scarcity_impact(self):
        '''Test that tailenders facing deliveries face significantly higher pressure than top order.'''
        d = self.scored[self.scored['in_scope_competition'].fillna(False)]
        top_order = d[d['wickets_in_hand'] >= 8]['pressure_score'].median()
        tail = d[d['wickets_in_hand'] <= 3]['pressure_score'].median()
        self.assertLess(top_order, tail, 'Tail order must face higher median pressure than top order!')

    def test_06_phase_progression(self):
        '''Test that death overs have higher median pressure than powerplay.'''
        d = self.scored[self.scored['in_scope_competition'].fillna(False)]
        pp = d[d['innings_phase'] == 'powerplay']['pressure_score'].median()
        death = d[d['innings_phase'] == 'death']['pressure_score'].median()
        self.assertLess(pp, death, 'Death overs must exhibit higher pressure than powerplay!')

    def test_07_super_over_highest_pressure(self):
        '''Test that super overs are classified in the extreme pressure range (>= 85).'''
        so = self.scored[self.scored['innings'] >= 3]
        if len(so) > 0:
            self.assertTrue((so['pressure_score'] >= 85.0).all(), 'Super overs must be high/extreme pressure!')

    def test_08_emerging_teams_exclusion_flag(self):
        '''Test that Emerging Teams T20 matches are properly flagged as out-of-scope.'''
        et = self.scored[self.scored['competition_scope'] == 'Emerging_T20']
        self.assertTrue((et['in_scope_competition'] == False).all(), 'Emerging teams must be marked out of scope!')

    def test_09_unlabelled_extras_isolated(self):
        '''Test that unlabelled-extra records remain flagged as ambiguous and unknown.'''
        unlabelled = self.scored[self.scored['unlabelled_extras'] == True]
        self.assertTrue((unlabelled['is_unknown_extra'] == True).all(), 'Unlabelled extras must be flagged as unknown extra!')
        self.assertTrue((unlabelled['legal_ball'] == False).all(), 'Unlabelled extras must not be classified as legal ball!')

    def test_10_match_outcome_relationship(self):
        '''Test that chasing team win rate decreases monotonically as pressure tier increases.'''
        chase = self.scored[(self.scored['innings'] == 2) & (self.scored['in_scope_competition'].fillna(False))].copy()
        # Merge match winner
        matches = pd.read_csv(BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv')
        chase = chase.merge(matches[['match_id', 'win_team_id']], on='match_id', how='left')
        chase['chase_won'] = (chase['win_team_id_y'] == chase['batting_team_id']).astype(int)
        
        tier_win = chase.groupby('pressure_tier', observed=False)['chase_won'].mean()
        # Verify strict monotonic decrease across pressure tiers
        self.assertGreater(tier_win['Low'], tier_win['Moderate'])
        self.assertGreater(tier_win['Moderate'], tier_win['High'])
        self.assertGreater(tier_win['High'], tier_win['Very High'])
        self.assertGreater(tier_win['Very High'], tier_win['Extreme'])

if __name__ == '__main__':
    unittest.main()
