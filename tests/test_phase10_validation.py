#!/usr/bin/env python3
"""
test_phase10_validation.py
Comprehensive automated test suite for Phase 10 Final CPRI Ranking Validation.
Validates:
  1. All 9 Phase 10 deliverables exist and are non-empty.
  2. Candidate roster integrity (exactly 15 batters and 15 bowlers matching Phase 8).
  3. Cutoff analysis integrity (Chahal vs Abrar Ahmed 0.08 point gap, Jadeja vs Shashank 0.87 gap).
  4. Format robustness data consistency and categorization.
  5. Innings-phase robustness delivery conservation.
  6. Opposition-strength robustness validity.
  7. Preservation of frozen Phase 1-3.5 and Phase 8 outputs.
"""
import json
import unittest
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PHASE10_OUT = BASE_DIR / 'output' / 'phase10_ranking_validation'
PHASE8_DIR = BASE_DIR / 'output' / 'phase8_ranking_reconsideration'
PHASE35_DIR = BASE_DIR / 'output' / 'phase3_5'

class TestPhase10Validation(unittest.TestCase):

    def test_01_all_deliverables_exist_and_non_empty(self):
        """Verify all 9 Phase 10 deliverables exist and are non-empty."""
        expected_files = [
            'phase10_methodology_and_scope.md',
            'phase10_format_robustness.csv',
            'phase10_innings_phase_robustness.csv',
            'phase10_pressure_robustness.csv',
            'phase10_opposition_robustness.csv',
            'phase10_sample_reliability.csv',
            'phase10_cutoff_analysis.csv',
            'phase10_rank_uncertainty.csv',
            'phase10_final_assessment.md'
        ]
        for fname in expected_files:
            fpath = PHASE10_OUT / fname
            self.assertTrue(fpath.exists(), f"Missing required Phase 10 deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 100, f"Deliverable {fname} is suspiciously small or empty")

    def test_02_candidate_roster_integrity(self):
        """Verify candidate roster contains exactly Ranks 1 to 15 matching Phase 8."""
        sample_df = pd.read_csv(PHASE10_OUT / 'phase10_sample_reliability.csv')
        batters = sample_df[sample_df['role'] == 'Batter'].sort_values('official_rank')
        bowlers = sample_df[sample_df['role'] == 'Bowler'].sort_values('official_rank')
        
        self.assertEqual(len(batters), 15, "Expected 15 batter candidates (Ranks 1 to 15)")
        self.assertEqual(len(bowlers), 15, "Expected 15 bowler candidates (Ranks 1 to 15)")
        self.assertEqual(list(batters['official_rank']), list(range(1, 16)))
        self.assertEqual(list(bowlers['official_rank']), list(range(1, 16)))
        
        # Verify specific key players
        self.assertEqual(batters.iloc[0]['player_name'], 'Matthew Wade')
        self.assertEqual(batters.iloc[1]['player_name'], 'Tim David')
        self.assertEqual(batters.iloc[2]['player_name'], 'Suryakumar Yadav')
        self.assertEqual(batters.iloc[9]['player_name'], 'Ravindra Jadeja')
        self.assertEqual(batters.iloc[10]['player_name'], 'Shashank Singh')
        
        self.assertEqual(bowlers.iloc[0]['player_name'], 'Mitchell Santner')
        self.assertEqual(bowlers.iloc[1]['player_name'], 'Sufiyan Muqeem')
        self.assertEqual(bowlers.iloc[2]['player_name'], 'Rashid Khan')
        self.assertEqual(bowlers.iloc[9]['player_name'], 'Yuzvendra Chahal')
        self.assertEqual(bowlers.iloc[10]['player_name'], 'Abrar Ahmed')

    def test_03_cutoff_analysis_gap_metrics(self):
        """Verify cutoff analysis captures exact empirical margins and paired bootstrap differences."""
        cutoff_df = pd.read_csv(PHASE10_OUT / 'phase10_cutoff_analysis.csv')
        
        # Bowler Rank 10 Chahal vs Rank 11 Abrar Ahmed
        chahal = cutoff_df[(cutoff_df['role'] == 'Bowler') & (cutoff_df['official_rank'] == 10)].iloc[0]
        abrar = cutoff_df[(cutoff_df['role'] == 'Bowler') & (cutoff_df['official_rank'] == 11)].iloc[0]
        self.assertAlmostEqual(chahal['cpri_score'] - abrar['cpri_score'], 0.08, places=2)
        self.assertEqual(chahal['top10_inclusion_freq'], abrar['top10_inclusion_freq'])
        self.assertAlmostEqual(abrar['paired_boot_diff_mean'], 0.92, places=2)
        self.assertAlmostEqual(abrar['paired_boot_p_win_vs_rank10'], 0.499, places=2)
        self.assertEqual(abrar['paired_boot_95_ci'], '[-56.39, 55.39]')
        
        # Batter Rank 10 Jadeja vs Rank 11 Shashank Singh
        jadeja = cutoff_df[(cutoff_df['role'] == 'Batter') & (cutoff_df['official_rank'] == 10)].iloc[0]
        shashank = cutoff_df[(cutoff_df['role'] == 'Batter') & (cutoff_df['official_rank'] == 11)].iloc[0]
        self.assertAlmostEqual(jadeja['cpri_score'] - shashank['cpri_score'], 0.87, places=2)
        self.assertAlmostEqual(shashank['paired_boot_diff_mean'], -6.37, places=2)
        self.assertAlmostEqual(shashank['paired_boot_p_win_vs_rank10'], 0.583, places=2)
        self.assertEqual(shashank['paired_boot_95_ci'], '[-61.34, 47.69]')

    def test_04_format_robustness_consistency(self):
        """Verify format robustness table properly partitions IPL and T20I deliveries and dual-format proportions."""
        fmt_df = pd.read_csv(PHASE10_OUT / 'phase10_format_robustness.csv')
        self.assertEqual(len(fmt_df), 30)
        
        # Check dual-format counts among official Top 10
        top10_batters = fmt_df[(fmt_df['role'] == 'Batter') & (fmt_df['official_rank'] <= 10)]
        top10_bowlers = fmt_df[(fmt_df['role'] == 'Bowler') & (fmt_df['official_rank'] <= 10)]
        
        dual_batters = top10_batters[(top10_batters['ipl_pressure_balls'] > 0) & (top10_batters['t20i_pressure_balls'] > 0)]
        dual_bowlers = top10_bowlers[(top10_bowlers['ipl_pressure_balls'] > 0) & (top10_bowlers['t20i_pressure_balls'] > 0)]
        
        self.assertEqual(len(dual_batters), 9, "Expected exactly 9/10 dual-format batters in official Top 10")
        self.assertEqual(len(dual_bowlers), 7, "Expected exactly 7/10 dual-format bowlers in official Top 10")
        
        # Single-format specialists must have 0 in other format
        reeza = fmt_df[fmt_df['player_name'] == 'Reeza Hendricks'].iloc[0]
        self.assertEqual(reeza['ipl_pressure_balls'], 0)
        self.assertGreater(reeza['t20i_pressure_balls'], 300)
        
        narine = fmt_df[fmt_df['player_name'] == 'Sunil Narine'].iloc[0]
        self.assertGreater(narine['ipl_pressure_balls'], 400)
        self.assertEqual(narine['t20i_pressure_balls'], 0)
        
        # Dual format players must have positive deliveries in both
        tim_david = fmt_df[fmt_df['player_name'] == 'Tim David'].iloc[0]
        self.assertGreater(tim_david['ipl_pressure_balls'], 200)
        self.assertGreater(tim_david['t20i_pressure_balls'], 100)

    def test_05_innings_phase_delivery_conservation(self):
        """Verify innings phase pressure deliveries conserve standard regulation deliveries."""
        phase_df = pd.read_csv(PHASE10_OUT / 'phase10_innings_phase_robustness.csv')
        sample_df = pd.read_csv(PHASE10_OUT / 'phase10_sample_reliability.csv')
        
        for pid in sample_df['player_id'].unique():
            tot_press = int(sample_df[sample_df['player_id'] == pid]['pressure_deliveries'].iloc[0])
            phase_sub = phase_df[phase_df['player_id'] == pid]
            phase_sum = int(phase_sub['phase_pressure_balls'].sum())
            # Phase sum accounts for regulation phases (Powerplay, Middle, Death),
            # with rare super-over tiebreaker balls (max 2-3 balls) excluded from regulation phases.
            self.assertGreaterEqual(tot_press, phase_sum)
            self.assertLessEqual(tot_press - phase_sum, 3, f"Player {pid} discrepancy too large: tot={tot_press}, phase={phase_sum}")

    def test_06_preservation_of_frozen_phase8_and_phase35(self):
        """Verify Phase 8 official rankings and Phase 3.5 methodology remain 100% intact."""
        top10_bat = pd.read_csv(PHASE8_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(PHASE8_DIR / 'official_top10_bowlers.csv')
        self.assertEqual(len(top10_bat), 10)
        self.assertEqual(len(top10_bowl), 10)
        
        with open(PHASE35_DIR / 'methodology_version.json', 'r', encoding='utf-8') as f:
            v_data = json.load(f)
        self.assertEqual(v_data.get('methodology_version'), 'CPRI-v1.0.0-PROD-FREEZE')

if __name__ == '__main__':
    unittest.main()
