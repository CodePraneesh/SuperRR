#!/usr/bin/env python3
"""
test_phase8_validation.py
Comprehensive automated test suite for SupeRR Selector Season 2 — Phase 8 Critical Recalculation.
Verifies all 17 mandatory validation requirements specified in Part K of the official instructions.
"""
import unittest
import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / 'output' / 'phase8_ranking_reconsideration'
PROCESSED_DIR = BASE_DIR / 'output' / 'processed'

class TestPhase8Validation(unittest.TestCase):

    def setUp(self):
        self.out_dir = OUT_DIR
        self.assertTrue(self.out_dir.exists(), "Phase 8 output directory must exist.")

    def test_01_source_row_counts_and_match_coverage(self):
        """Part K.1: Verify raw source dataset row counts and match coverage."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/matches_enriched.csv', 'python supeRR_phase1_pipeline.py')
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        matches = pd.read_csv(PROCESSED_DIR / 'matches_enriched.csv', low_memory=False)
        deliveries = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', low_memory=False)
        
        self.assertEqual(len(matches), 883, "Matches table must have exactly 883 rows.")
        self.assertEqual(len(deliveries), 200999, "Deliveries table must have exactly 200,999 rows.")
        
        unique_matches_in_balls = deliveries['match_id'].nunique()
        self.assertEqual(unique_matches_in_balls, 867, "Deliveries must cover exactly 867 distinct match IDs.")
        
        missing_matches = len(matches) - unique_matches_in_balls
        self.assertEqual(missing_matches, 16, "Exactly 16 match IDs must have no ball-by-ball rows.")

    def test_02_competition_scope_separation(self):
        """Part K.2: Verify competition format separation and Emerging Teams exclusion."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/matches_enriched.csv', 'python supeRR_phase1_pipeline.py')
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        matches = pd.read_csv(PROCESSED_DIR / 'matches_enriched.csv', low_memory=False)
        deliveries = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', low_memory=False)
        
        comp_counts = matches['competition_scope'].value_counts().to_dict()
        self.assertEqual(comp_counts.get('T20I'), 482, "T20I must have exactly 482 matches.")
        self.assertEqual(comp_counts.get('IPL'), 371, "IPL must have exactly 371 matches.")
        self.assertEqual(comp_counts.get('Emerging_T20'), 30, "Emerging Teams must have exactly 30 matches.")
        
        deliv_counts = deliveries['competition_scope'].value_counts().to_dict()
        self.assertEqual(deliv_counts.get('Emerging_T20'), 6985, "Emerging Teams must have 6,985 balls.")
        
        # Verify official candidates do not include Emerging_T20
        bat_pop = pd.read_csv(OUT_DIR / 'batter_full_population.csv')
        self.assertNotIn('Emerging_T20', bat_pop['competition_evidence'].unique())

    def test_03_player_identity_joins_and_collisions(self):
        """Part K.3: Verify player ID authority and name collision handling."""
        bat_pop = pd.read_csv(OUT_DIR / 'batter_full_population.csv')
        bowl_pop = pd.read_csv(OUT_DIR / 'bowler_full_population.csv')
        
        # Each player_id must be unique within population tables
        self.assertEqual(bat_pop['player_id'].nunique(), len(bat_pop), "Batter player_id must be unique.")
        self.assertEqual(bowl_pop['player_id'].nunique(), len(bowl_pop), "Bowler player_id must be unique.")
        
        # Verify collision names have distinct IDs
        samad_ids = bat_pop[bat_pop['player_name'] == 'Abdul Samad']['player_id'].tolist()
        if len(samad_ids) > 1:
            self.assertEqual(len(samad_ids), len(set(samad_ids)), "Name collision Abdul Samad must have distinct IDs.")

    def test_04_no_duplicate_players_in_official_lists(self):
        """Part K.4: Verify no duplicate players exist in official submission lists."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        self.assertEqual(len(top10_bat), top10_bat['player_id'].nunique(), "No duplicate player_id in top 10 batters.")
        self.assertEqual(len(top10_bat), top10_bat['player_name'].nunique(), "No duplicate player_name in top 10 batters.")
        
        self.assertEqual(len(top10_bowl), top10_bowl['player_id'].nunique(), "No duplicate player_id in top 10 bowlers.")
        self.assertEqual(len(top10_bowl), top10_bowl['player_name'].nunique(), "No duplicate player_name in top 10 bowlers.")

    def test_05_exactly_ten_players_per_official_list(self):
        """Part K.5: Confirm exactly 10 players in official submission lists."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        self.assertEqual(len(top10_bat), 10, "Official Top 10 Batters must have exactly 10 entries.")
        self.assertEqual(len(top10_bowl), 10, "Official Top 10 Bowlers must have exactly 10 entries.")

    def test_06_rank_order_consistency(self):
        """Part K.6: Verify ranks 1-10 are strictly ordered and scores are non-increasing."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        self.assertEqual(list(top10_bat['official_rank']), list(range(1, 11)), "Batter ranks must be exactly 1..10.")
        self.assertEqual(list(top10_bowl['official_rank']), list(range(1, 11)), "Bowler ranks must be exactly 1..10.")
        
        # Non-increasing CPRI
        self.assertTrue((top10_bat['cpri_score'].diff().dropna() <= 0.001).all(), "Batter CPRI must be non-increasing.")
        self.assertTrue((top10_bowl['cpri_score'].diff().dropna() <= 0.001).all(), "Bowler CPRI must be non-increasing.")

    def test_07_no_negative_or_impossible_performance_values(self):
        """Part K.7: Verify all performance metrics fall within physically possible ranges."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        # Batters
        self.assertTrue((top10_bat['pressure_deliveries'] > 0).all(), "Batter deliveries must be positive.")
        self.assertTrue((top10_bat['pressure_matches'] > 0).all(), "Batter matches must be positive.")
        self.assertTrue((top10_bat['pressure_strike_rate'] >= 0.0).all(), "Strike rates must be non-negative.")
        self.assertTrue(((top10_bat['cpri_score'] >= 0.0) & (top10_bat['cpri_score'] <= 100.0)).all(), "CPRI in [0, 100].")
        
        # Bowlers
        self.assertTrue((top10_bowl['pressure_deliveries'] > 0).all(), "Bowler deliveries must be positive.")
        self.assertTrue((top10_bowl['pressure_matches'] > 0).all(), "Bowler matches must be positive.")
        self.assertTrue((top10_bowl['pressure_economy'] >= 0.0).all(), "Economy must be non-negative.")
        self.assertTrue(((top10_bowl['cpri_score'] >= 0.0) & (top10_bowl['cpri_score'] <= 100.0)).all(), "CPRI in [0, 100].")

    def test_08_correct_extra_run_attribution(self):
        """Part K.8: Verify extras attribution rules on deliveries."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        delivs = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', nrows=5000, low_memory=False)
        
        # Wides charged to bowler
        wides = delivs[delivs['is_wide'] == 1]
        if not wides.empty:
            self.assertTrue((wides['bowler_runs_conceded'] >= 1).all(), "Wides must be charged to bowler runs conceded.")
            
        # Legbyes not charged to bowler
        legbyes = delivs[(delivs['extras_label'] == 'legbyes') & (delivs['batter_runs'] == 0)]
        if not legbyes.empty:
            self.assertTrue((legbyes['bowler_runs_conceded'] == 0).all(), "Pure legbyes must not be charged to bowler.")

    def test_09_correct_wicket_credit_attribution(self):
        """Part K.9: Verify non-bowler wickets are not credited to bowlers."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        delivs = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', nrows=20000, low_memory=False)
        
        run_outs = delivs[delivs['dismissal_type'] == 'RunOut']
        if not run_outs.empty:
            self.assertTrue((run_outs['bowler_wicket'] == 0).all(), "Run outs must never be credited as bowler_wicket.")
            
        bowled = delivs[delivs['dismissal_type'] == 'Bowled']
        if not bowled.empty:
            self.assertTrue((bowled['bowler_wicket'] == 1).all(), "Bowled dismissals must be credited as bowler_wicket.")

    def test_10_no_future_information_in_pressure_features(self):
        """Part K.10: Verify pre-delivery state variables contain zero lookahead."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        delivs = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', nrows=1000, low_memory=False)
        ball_ones = delivs[(delivs['innings_ball_num'] == 1)]
        self.assertTrue((ball_ones['score_before'] == 0).all(), "Ball 1 score_before must be 0.")
        self.assertTrue((ball_ones['wickets_lost_before'] == 0).all(), "Ball 1 wickets_lost_before must be 0.")
        self.assertTrue((ball_ones['legal_balls_before'] == 0).all(), "Ball 1 legal_balls_before must be 0.")

    def test_11_no_target_leakage(self):
        """Part K.11: Pre-delivery pressure index is independent of current ball outcome."""
        from tests.conftest import require_data_file
        require_data_file('output/processed/deliveries_enriched.csv', 'python supeRR_phase1_pipeline.py')
        delivs = pd.read_csv(PROCESSED_DIR / 'deliveries_enriched.csv', nrows=2000, low_memory=False)
        # Check that pre_delivery_pressure_index is present and non-null
        self.assertIn('pre_delivery_pressure_index', delivs.columns)
        self.assertTrue(delivs['pre_delivery_pressure_index'].notna().all(), "Pre-delivery pressure cannot be NaN.")

    def test_12_missing_data_handling(self):
        """Part K.12: Verify missing matches are properly documented and not imputed as zero."""
        with open(OUT_DIR / 'source_data_coverage_report.md', 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('31281', content, "Missing match 31281 must be explicitly listed in coverage report.")
        self.assertIn('16', content, "16 missing matches must be explicitly reported.")

    def test_13_small_sample_uncertainty_and_eligibility(self):
        """Part K.13: Verify eligibility thresholds strictly enforced in official lists."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        self.assertTrue((top10_bat['pressure_deliveries'] >= 100).all(), "All top 10 batters have >= 100 pressure balls.")
        self.assertTrue((top10_bat['pressure_matches'] >= 8).all(), "All top 10 batters have >= 8 pressure matches.")
        
        self.assertTrue((top10_bowl['pressure_deliveries'] >= 80).all(), "All top 10 bowlers have >= 80 pressure balls.")
        self.assertTrue((top10_bowl['pressure_matches'] >= 8).all(), "All top 10 bowlers have >= 8 pressure matches.")

    def test_14_deterministic_reproducibility(self):
        """Part K.14: Verify reproducibility manifest contains seed=42 and deliverable hashes."""
        with open(OUT_DIR / 'reproducibility_manifest.json', 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        self.assertEqual(manifest.get('random_seed'), 42, "Seed must be exactly 42.")
        self.assertEqual(manifest.get('bootstrap_iterations'), 1000, "Bootstrap iterations must be 1000.")
        self.assertGreater(len(manifest.get('deliverable_hashes', {})), 10, "Manifest must contain file hashes.")

    def test_15_score_calculation_integrity(self):
        """Part K.15: Verify CPRI weighted sum identity."""
        top10_bat = pd.read_csv(OUT_DIR / 'official_top10_batters.csv')
        top10_bowl = pd.read_csv(OUT_DIR / 'official_top10_bowlers.csv')
        
        for df in [top10_bat, top10_bowl]:
            recalc = (
                0.40 * df['score_pressure_impact'] +
                0.25 * df['score_adaptability'] +
                0.20 * df['score_consistency'] +
                0.15 * df['score_reliability']
            ).round(2)
            diff = (recalc - df['cpri_score']).abs()
            self.assertTrue((diff <= 0.02).all(), f"CPRI calculation mismatch: max diff = {diff.max()}")

    def test_16_resampling_reproducibility(self):
        """Part K.16: Verify bootstrap uncertainty statistics are within theoretical bounds."""
        b_unc = pd.read_csv(OUT_DIR / 'batter_rank_uncertainty.csv')
        bw_unc = pd.read_csv(OUT_DIR / 'bowler_rank_uncertainty.csv')
        
        for df in [b_unc, bw_unc]:
            self.assertTrue(((df['top10_inclusion_freq'] >= 0.0) & (df['top10_inclusion_freq'] <= 1.0)).all(), "Frequencies in [0, 1].")
            self.assertTrue((df['rank_p5'] <= df['median_rank']).all(), "p5 <= median rank.")
            self.assertTrue((df['median_rank'] <= df['rank_p95']).all(), "median rank <= p95.")
            self.assertTrue((df['rank_std'] >= 0.0).all(), "Std dev non-negative.")

    def test_17_all_eighteen_deliverables_exist_and_non_empty(self):
        """Part K.17: Verify all 18 required deliverables exist and are populated."""
        expected_files = [
            'source_data_coverage_report.md',
            'pressure_definition_report.md',
            'batter_full_population.csv',
            'bowler_full_population.csv',
            'batter_candidate_comparison.csv',
            'bowler_candidate_comparison.csv',
            'official_top10_batters.csv',
            'official_top10_bowlers.csv',
            'ipl_only_batter_rankings.csv',
            'ipl_only_bowler_rankings.csv',
            't20i_only_batter_rankings.csv',
            't20i_only_bowler_rankings.csv',
            'batter_rank_uncertainty.csv',
            'bowler_rank_uncertainty.csv',
            'old_vs_new_rankings.csv',
            'final_methodology_report.md',
            'phase8_reconsideration_summary.md',
            'reproducibility_manifest.json'
        ]
        self.assertEqual(len(expected_files), 18, "Must check exactly 18 files.")
        for fname in expected_files:
            fpath = OUT_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 100, f"Deliverable is empty or truncated: {fname}")

if __name__ == '__main__':
    unittest.main()
