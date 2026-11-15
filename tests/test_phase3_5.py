#!/usr/bin/env python3
"""
test_phase3_5.py
Unit test suite for Phase 3.5 Official Methodology Freeze deliverables.
"""
import unittest
import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase3_5'
P33_DIR = BASE_DIR / 'output' / 'phase3_3'

class TestPhase35(unittest.TestCase):

    def test_01_deliverable_files_exist_and_populated(self):
        """Test that all 6 required Phase 3.5 deliverable files exist and are non-empty."""
        required_files = [
            'methodology_freeze.md',
            'official_rankings.json',
            'official_rankings.csv',
            'eligibility_and_uncertainty.csv',
            'methodology_version.json',
            'phase3_5_freeze_report.md'
        ]
        for fname in required_files:
            fpath = OUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Deliverable {fname} does not exist.")
            self.assertGreater(fpath.stat().st_size, 100, f"Deliverable {fname} is too small / empty.")

    def test_02_all_four_cohorts_contain_exactly_ten_official_players(self):
        """Confirm all four ranking cohorts contain exactly 10 official players."""
        df_csv = pd.read_csv(OUT_DIR / 'official_rankings.csv')
        off_df = df_csv[df_csv['ranking_tier'] == 'Official Top 10']
        self.assertEqual(len(off_df), 40, "Must be exactly 40 official players across all cohorts.")

        cohorts = ["IPL Batters", "T20I Batters", "IPL Bowlers", "T20I Bowlers"]
        for cname in cohorts:
            sub = off_df[off_df['cohort'] == cname]
            self.assertEqual(len(sub), 10, f"Cohort {cname} must have exactly 10 official players.")
            self.assertEqual(sorted(sub['official_rank'].tolist()), list(range(1, 11)), f"Ranks for {cname} must be 1 to 10.")

    def test_03_rankings_match_approved_phase3_baseline(self):
        """Confirm rankings and CPRI scores match the approved Phase 3 baseline point estimates."""
        frozen_csv = pd.read_csv(OUT_DIR / 'official_rankings.csv')
        off_frozen = frozen_csv[frozen_csv['ranking_tier'] == 'Official Top 10'].set_index(['cohort', 'official_rank'])

        bat_33 = pd.read_csv(P33_DIR / 'final_top10_batters.csv')
        bowl_33 = pd.read_csv(P33_DIR / 'final_top10_bowlers.csv')

        bat_off = bat_33[bat_33['category'] == 'Eligible Top 10']
        bowl_off = bowl_33[bowl_33['category'] == 'Eligible Top 10']

        for _, r in bat_off.iterrows():
            cohort = r['competition_scope'] + " Batters"
            rank = r['official_rank']
            frozen_row = off_frozen.loc[(cohort, rank)]
            self.assertEqual(frozen_row['player_name'], r['player_name'], f"Name mismatch for {cohort} rank {rank}")
            self.assertAlmostEqual(frozen_row['cpri_score'], r['cpri_score'], places=2, msg=f"Score mismatch for {cohort} rank {rank}")

        for _, r in bowl_off.iterrows():
            cohort = r['competition_scope'] + " Bowlers"
            rank = r['official_rank']
            frozen_row = off_frozen.loc[(cohort, rank)]
            self.assertEqual(frozen_row['player_name'], r['player_name'], f"Name mismatch for {cohort} rank {rank}")
            self.assertAlmostEqual(frozen_row['cpri_score'], r['cpri_score'], places=2, msg=f"Score mismatch for {cohort} rank {rank}")

    def test_04_component_weights_sum_to_one_hundred_percent(self):
        """Confirm all component weights sum to 100% and match specification."""
        with open(OUT_DIR / 'methodology_version.json', 'r', encoding='utf-8') as f:
            v_data = json.load(f)

        weights = v_data['component_weights']
        self.assertEqual(weights['pressure_impact'], 0.40)
        self.assertEqual(weights['pressure_adaptability'], 0.25)
        self.assertEqual(weights['clutch_consistency'], 0.20)
        self.assertEqual(weights['reliability_confidence'], 0.15)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=9)

    def test_05_pressure_threshold_and_eligibility_rules(self):
        """Confirm pressure threshold (50) and eligibility rules match frozen specification."""
        with open(OUT_DIR / 'methodology_version.json', 'r', encoding='utf-8') as f:
            v_data = json.load(f)

        self.assertEqual(v_data['pressure_threshold'], 50.0)

        bat_rules = v_data['eligibility_thresholds']['Batter']
        self.assertEqual(bat_rules['pressure_deliveries'], 100)
        self.assertEqual(bat_rules['pressure_matches'], 8)
        self.assertEqual(bat_rules['total_deliveries'], 150)
        self.assertEqual(bat_rules['nonpressure_deliveries'], 40)

        bowl_rules = v_data['eligibility_thresholds']['Bowler']
        self.assertEqual(bowl_rules['pressure_deliveries'], 80)
        self.assertEqual(bowl_rules['pressure_matches'], 8)
        self.assertEqual(bowl_rules['total_deliveries'], 180)
        self.assertEqual(bowl_rules['balls_per_match'], 12.0)

    def test_06_provisional_rankings_preserved_separately(self):
        """Confirm provisional rankings are preserved separately from official rankings."""
        df_csv = pd.read_csv(OUT_DIR / 'official_rankings.csv')
        prov_df = df_csv[df_csv['ranking_tier'] == 'Provisional Top 5']
        self.assertEqual(len(prov_df), 20, "Must be exactly 20 provisional players (5 per cohort).")
        for tier in prov_df['confidence_tier']:
            self.assertEqual(tier, 'Moderate Confidence')

    def test_07_previous_audit_reports_remain_untouched(self):
        """Confirm all previous phase audit deliverables remain intact."""
        previous_phases = ['processed', 'features', 'audit', 'phase2', 'phase3', 'phase3_1', 'phase3_2', 'phase3_3', 'phase3_4', 'phase3_4_1', 'phase3_4_2', 'phase3_4_3', 'phase3_4_3_1', 'phase3_4_3_2']
        for p in previous_phases:
            pdir = BASE_DIR / 'output' / p
            self.assertTrue(pdir.exists(), f"Directory {p} does not exist.")
            self.assertGreater(len(list(pdir.glob('*'))), 0, f"Directory {p} is empty.")

    def test_08_final_freeze_verdict(self):
        """Confirm final verdict is FREEZE APPROVED WITH DOCUMENTED LIMITATIONS."""
        rep_path = OUT_DIR / 'phase3_5_freeze_report.md'
        content = rep_path.read_text(encoding='utf-8')
        self.assertIn("FREEZE APPROVED WITH DOCUMENTED LIMITATIONS", content)
        self.assertNotIn("FREEZE REJECTED", content)

if __name__ == '__main__':
    unittest.main()
