#!/usr/bin/env python3
"""
tests/test_cpri_32.py
Unit tests for Phase 3.2: Official Batter Ranking Audit & Refinement.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_2'

class TestCPRI32(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.2 deliverables for test validation...")
        cls.elig_df = pd.read_csv(OUTPUT_DIR / 'batter_eligibility_analysis.csv')
        cls.adapt_df = pd.read_csv(OUTPUT_DIR / 'adaptability_diagnostics.csv')
        cls.wade_df = pd.read_csv(OUTPUT_DIR / 'matthew_wade_audit.csv')
        cls.top10_df = pd.read_csv(OUTPUT_DIR / 'revised_top10_batters.csv')
        cls.comp_df = pd.read_csv(OUTPUT_DIR / 'ranking_comparison.csv')
        print("Loaded Phase 3.2 datasets.")

    def test_01_deliverable_files_exist_and_populated(self):
        """Test that all 6 required Phase 3.2 deliverables exist and contain records."""
        expected_files = [
            'batter_ranking_audit.md',
            'batter_eligibility_analysis.csv',
            'adaptability_diagnostics.csv',
            'matthew_wade_audit.csv',
            'revised_top10_batters.csv',
            'ranking_comparison.csv'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_eligibility_tier_assignment(self):
        """Test that eligibility rules correctly require M_p >= 8, N_p >= 100, N_tot >= 150."""
        # High Confidence batters must meet all 3 thresholds
        high_conf = self.elig_df[self.elig_df['tier_phase3_2_strict'] == 'High Confidence']
        self.assertTrue((high_conf['pressure_matches'] >= 8).all(), "All High Confidence must have >= 8 pressure matches!")
        self.assertTrue((high_conf['pressure_deliveries'] >= 100).all(), "All High Confidence must have >= 100 pressure balls!")
        self.assertTrue((high_conf['total_deliveries'] >= 150).all(), "All High Confidence must have >= 150 total balls!")

        # Verify flagged low-match players are NOT in High Confidence:
        karun = self.elig_df[(self.elig_df['player_name'] == 'Karun Nair') & (self.elig_df['competition_scope'] == 'IPL')]
        self.assertEqual(karun['tier_phase3_2_strict'].iloc[0], 'Moderate Confidence')

        masood = self.elig_df[(self.elig_df['player_name'] == 'Shan Masood') & (self.elig_df['competition_scope'] == 'T20I')]
        self.assertEqual(masood['tier_phase3_2_strict'].iloc[0], 'Moderate Confidence')

    def test_03_robust_adaptability_scaling_properties(self):
        """Test that robust sigmoid scaling produces scores bounded in [0, 100] with strict monotonicity."""
        for scope in ['IPL', 'T20I']:
            s = self.adapt_df[self.adapt_df['competition_scope'] == scope]
            self.assertTrue((s['score_adaptability_p32_robust'] >= 0.0).all())
            self.assertTrue((s['score_adaptability_p32_robust'] <= 100.0).all())
            
            # Monotonicity check: sort by shrunk adaptability and ensure scores are non-decreasing
            s_sorted = s.sort_values('shrunk_adaptability', ascending=True)
            diffs = np.diff(s_sorted['score_adaptability_p32_robust'].values)
            self.assertTrue((diffs >= -1e-6).all(), f"Robust adaptability scores in {scope} must be monotonically non-decreasing!")

    def test_04_matthew_wade_audit_facts(self):
        """Verify delivery and match audit facts for Matthew Wade in T20I."""
        self.assertEqual(len(self.wade_df), 12, "Matthew Wade must have exactly 12 pressure matches in T20I!")
        self.assertTrue(self.wade_df['is_positive_match'].all(), "All 12 matches for Wade must have positive net impact (100% positive match ratio)!")
        self.assertEqual(int(self.wade_df['actual_dismissals'].sum()), 2, "Wade must have exactly 2 dismissals across pressure deliveries!")
        self.assertEqual(int(self.wade_df['actual_runs'].sum()), 281, "Wade must have 281 actual runs across pressure deliveries!")
        self.assertEqual(int(self.wade_df['pressure_deliveries'].sum()), 160, "Wade must have 160 pressure deliveries in T20I!")

    def test_05_revised_top10_rankings_integrity(self):
        """Test that revised Top 10 has 10 batters per scope and excludes ineligible players."""
        self.assertEqual(len(self.top10_df), 20, "Revised Top 10 must have exactly 20 rows (10 IPL, 10 T20I)!")
        ipl_top = self.top10_df[self.top10_df['competition_scope'] == 'IPL']
        t20i_top = self.top10_df[self.top10_df['competition_scope'] == 'T20I']

        # Confirm Rinku Singh is #1 in IPL, Wade is #1 in T20I
        self.assertEqual(ipl_top.iloc[0]['player_name'], 'Rinku Singh')
        self.assertEqual(t20i_top.iloc[0]['player_name'], 'Matthew Wade')

        # Confirm Karun Nair and Shan Masood are excluded from revised Top 10
        self.assertNotIn('Karun Nair', ipl_top['player_name'].values)
        self.assertNotIn('Shan Masood', t20i_top['player_name'].values)

if __name__ == '__main__':
    unittest.main()
