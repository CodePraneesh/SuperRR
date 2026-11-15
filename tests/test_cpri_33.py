#!/usr/bin/env python3
"""
tests/test_cpri_33.py
Unit tests for Phase 3.3: Unified Ranking Audit & Verification.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output' / 'phase3_3'

class TestCPRI33(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 3.3 deliverables for test validation...")
        cls.bat_conf = pd.read_csv(OUTPUT_DIR / 'batter_confidence_audit.csv')
        cls.bowl_conf = pd.read_csv(OUTPUT_DIR / 'bowler_confidence_audit.csv')
        cls.adapt_rep = pd.read_csv(OUTPUT_DIR / 'adaptability_stability_report.csv')
        cls.consist_rep = pd.read_csv(OUTPUT_DIR / 'consistency_audit.csv')
        cls.top_bat = pd.read_csv(OUTPUT_DIR / 'final_top10_batters.csv')
        cls.top_bowl = pd.read_csv(OUTPUT_DIR / 'final_top10_bowlers.csv')
        cls.bat_comp = pd.read_csv(OUTPUT_DIR / 'batter_ranking_comparison.csv')
        cls.bowl_comp = pd.read_csv(OUTPUT_DIR / 'bowler_ranking_comparison.csv')
        print("Loaded Phase 3.3 datasets.")

    def test_01_all_10_deliverables_exist_and_populated(self):
        """Test that all 10 required Phase 3.3 deliverables exist and are non-empty."""
        expected_files = [
            'unified_ranking_audit.md',
            'batter_confidence_audit.csv',
            'bowler_confidence_audit.csv',
            'adaptability_stability_report.csv',
            'consistency_audit.csv',
            'batter_ranking_comparison.csv',
            'bowler_ranking_comparison.csv',
            'final_top10_batters.csv',
            'final_top10_bowlers.csv',
            'phase3_3_validation_report.md'
        ]
        for fname in expected_files:
            fpath = OUTPUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"File {fname} is empty!")

    def test_02_independent_score_validation(self):
        """Test that CPRI = 0.40*Imp + 0.25*Adapt + 0.20*Cons + 0.15*Rel holds exactly for all players."""
        for df, name in [(self.top_bat, 'Batters'), (self.top_bowl, 'Bowlers')]:
            recalc = (
                0.40 * df['score_pressure_impact'] +
                0.25 * df['score_adaptability'] +
                0.20 * df['score_consistency'] +
                0.15 * df['score_reliability']
            ).round(2)
            diff = (recalc - df['cpri_score']).abs()
            self.assertTrue((diff <= 0.01).all(), f"Independent score discrepancy found in {name}!")

    def test_03_bowler_workload_and_part_time_exclusion(self):
        """Verify that part-time bowlers (Ayush Badoni, Tristan Stubbs, Aiden Markram) are excluded from official Top 10."""
        ipl_bowl_top = self.top_bowl[(self.top_bowl['competition_scope'] == 'IPL') & (self.top_bowl['category'] == 'Eligible Top 10')]
        t20i_bowl_top = self.top_bowl[(self.top_bowl['competition_scope'] == 'T20I') & (self.top_bowl['category'] == 'Eligible Top 10')]

        self.assertNotIn('Ayush Badoni', ipl_bowl_top['player_name'].values)
        self.assertNotIn('Tristan Stubbs', ipl_bowl_top['player_name'].values)
        self.assertNotIn('Aiden Markram', t20i_bowl_top['player_name'].values)
        self.assertNotIn('Mark Watt', t20i_bowl_top['player_name'].values)

    def test_04_provisional_player_classification(self):
        """Verify that low-sample entries (Lungi Ngidi in IPL, Tabraiz Shamsi in T20I, Karun Nair, Shan Masood) are Provisional."""
        ipl_bowl_prov = self.top_bowl[(self.top_bowl['competition_scope'] == 'IPL') & (self.top_bowl['category'] == 'Provisional Top 5')]
        t20i_bowl_prov = self.top_bowl[(self.top_bowl['competition_scope'] == 'T20I') & (self.top_bowl['category'] == 'Provisional Top 5')]
        ipl_bat_prov = self.top_bat[(self.top_bat['competition_scope'] == 'IPL') & (self.top_bat['category'] == 'Provisional Top 5')]
        t20i_bat_prov = self.top_bat[(self.top_bat['competition_scope'] == 'T20I') & (self.top_bat['category'] == 'Provisional Top 5')]

        self.assertIn('Lungi Ngidi', ipl_bowl_prov['player_name'].values)
        self.assertIn('Tabraiz Shamsi', t20i_bowl_prov['player_name'].values)
        self.assertIn('Karun Nair', ipl_bat_prov['player_name'].values)
        self.assertIn('Shan Masood', t20i_bat_prov['player_name'].values)

    def test_05_certified_top10_champions(self):
        """Verify the #1 certified clutch players for IPL and T20I across both disciplines."""
        ipl_bat = self.top_bat[(self.top_bat['competition_scope'] == 'IPL') & (self.top_bat['category'] == 'Eligible Top 10')]
        t20i_bat = self.top_bat[(self.top_bat['competition_scope'] == 'T20I') & (self.top_bat['category'] == 'Eligible Top 10')]
        ipl_bowl = self.top_bowl[(self.top_bowl['competition_scope'] == 'IPL') & (self.top_bowl['category'] == 'Eligible Top 10')]
        t20i_bowl = self.top_bowl[(self.top_bowl['competition_scope'] == 'T20I') & (self.top_bowl['category'] == 'Eligible Top 10')]

        self.assertEqual(ipl_bat.iloc[0]['player_name'], 'Rinku Singh')
        self.assertEqual(t20i_bat.iloc[0]['player_name'], 'Matthew Wade')
        self.assertEqual(ipl_bowl.iloc[0]['player_name'], 'Matheesha Pathirana')
        self.assertEqual(t20i_bowl.iloc[0]['player_name'], 'Sufiyan Muqeem')

if __name__ == '__main__':
    unittest.main()
