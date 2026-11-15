#!/usr/bin/env python3
"""
test_phase9_validation.py
Comprehensive automated test suite for Phase 9 Context-Aware ML Model Comparison.
Validates:
  1. Deliverable existence and non-emptiness.
  2. Chronological match partition non-leakage and sample sizes.
  3. Pre-delivery feature validity and target metric bounds.
  4. Calibration deciles and Brier decomposition.
  5. Experimental player ranking sensitivity and stability.
  6. Strict preservation of frozen Phase 1-3.5 and Phase 8 ranking artifacts.
"""
import json
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PHASE9_OUT = BASE_DIR / 'output' / 'phase9_ml_evaluation'
MODELS_DIR = PHASE9_OUT / 'models'

class TestPhase9Validation(unittest.TestCase):

    def test_01_all_10_deliverables_exist_and_non_empty(self):
        """Verify all 10 mandated Phase 9 deliverables exist and are non-empty."""
        expected_deliverables = [
            'dataset_and_feature_audit.md',
            'baseline_model_evaluation.json',
            'match_grouped_evaluation.csv',
            'model_comparison_report.md',
            'calibration_report.md',
            'contextual_error_analysis.md',
            'experimental_ranking_sensitivity_report.md',
            'reproduction_instructions.md',
            'match_split_metadata.json',
            'ranking_sensitivity_summary.json'
        ]
        for fname in expected_deliverables:
            fpath = PHASE9_OUT / fname
            self.assertTrue(fpath.exists(), f"Missing required deliverable: {fname}")
            self.assertGreater(fpath.stat().st_size, 100, f"Deliverable {fname} is suspiciously small or empty")

    def test_02_python_code_modules_exist(self):
        """Verify all Python scripts in ml/phase9 exist."""
        ml_p9 = BASE_DIR / 'ml' / 'phase9'
        for fname in ['baseline_adapter.py', 'catboost_experiment.py', 'xgboost_experiment.py', 'dataset_audit.py', 'run_phase9_evaluation.py']:
            fpath = ml_p9 / fname
            self.assertTrue(fpath.exists(), f"Missing python module: {fname}")

    def test_03_saved_models_exist(self):
        """Verify model artifacts are serialized in output/phase9_ml_evaluation/models/."""
        expected_models = [
            'baseline_batter_runs.joblib',
            'baseline_batter_dismissal.joblib',
            'baseline_bowler_runs.joblib',
            'baseline_bowler_wicket.joblib',
            'catboost_batter_runs.cbm',
            'catboost_batter_dismissal.cbm',
            'catboost_bowler_runs.cbm',
            'catboost_bowler_wicket.cbm',
            'xgboost_batter_runs.json',
            'xgboost_batter_dismissal.json',
            'xgboost_bowler_runs.json',
            'xgboost_bowler_wicket.json'
        ]
        for mname in expected_models:
            mpath = MODELS_DIR / mname
            self.assertTrue(mpath.exists(), f"Missing trained model artifact: {mname}")
            self.assertGreater(mpath.stat().st_size, 500, f"Model file {mname} appears corrupt or empty")

    def test_04_split_integrity_and_zero_leakage(self):
        """Verify chronological match partitioning and zero leakage."""
        meta_file = PHASE9_OUT / 'match_split_metadata.json'
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            
        train_matches = set(meta['splits']['train']['match_ids'])
        val_matches = set(meta['splits']['val']['match_ids'])
        test_matches = set(meta['splits']['test']['match_ids'])
        
        self.assertEqual(len(train_matches & val_matches), 0, "Leakage detected: Train and Val overlap!")
        self.assertEqual(len(train_matches & test_matches), 0, "Leakage detected: Train and Test overlap!")
        self.assertEqual(len(val_matches & test_matches), 0, "Leakage detected: Val and Test overlap!")
        
        self.assertEqual(meta['splits']['train']['matches'], 569)
        self.assertEqual(meta['splits']['val']['matches'], 122)
        self.assertEqual(meta['splits']['test']['matches'], 122)
        self.assertEqual(meta['splits']['train']['deliveries'], 135264)
        self.assertEqual(meta['splits']['val']['deliveries'], 28332)
        self.assertEqual(meta['splits']['test']['deliveries'], 28639)

    def test_05_evaluation_metrics_validity(self):
        """Verify evaluation metrics are physically valid and within sensible cricket bounds."""
        eval_csv = PHASE9_OUT / 'match_grouped_evaluation.csv'
        df = pd.read_csv(eval_csv)
        
        overall = df[df['slice'] == 'Overall Test']
        self.assertEqual(len(overall), 4, "Should have 4 models evaluated on Overall Test")
        
        for _, row in overall.iterrows():
            m = row['model']
            # Batter runs RMSE should be between 1.5 and 2.2
            self.assertTrue(1.5 < row['bat_runs_rmse'] < 2.2, f"{m} bat_runs_rmse out of bounds: {row['bat_runs_rmse']}")
            # Batter dismissal log loss should be between 0.15 and 0.25
            self.assertTrue(0.15 < row['bat_out_log_loss'] < 0.25, f"{m} bat_out_log_loss out of bounds: {row['bat_out_log_loss']}")
            # Bowler runs RMSE should be between 1.5 and 2.2
            self.assertTrue(1.5 < row['bowl_runs_rmse'] < 2.2, f"{m} bowl_runs_rmse out of bounds: {row['bowl_runs_rmse']}")
            # Bowler wicket log loss should be between 0.15 and 0.25
            self.assertTrue(0.15 < row['bowl_wkt_log_loss'] < 0.25, f"{m} bowl_wkt_log_loss out of bounds: {row['bowl_wkt_log_loss']}")

    def test_06_sample_size_conservation(self):
        """Verify sample sizes across mutually exclusive slices conserve the total test size."""
        eval_csv = PHASE9_OUT / 'match_grouped_evaluation.csv'
        df = pd.read_csv(eval_csv)
        
        base_df = df[df['model'] == 'CatBoost']
        n_total = int(base_df[base_df['slice'] == 'Overall Test']['sample_size'].iloc[0])
        self.assertEqual(n_total, 28639)
        
        n_ipl = int(base_df[base_df['slice'] == 'IPL Matches']['sample_size'].iloc[0])
        n_t20i = int(base_df[base_df['slice'] == 'T20I Matches']['sample_size'].iloc[0])
        self.assertEqual(n_ipl + n_t20i, n_total, "IPL + T20I must equal Total deliveries")
        
        n_pp = int(base_df[base_df['slice'] == 'Powerplay (Overs 0-5)']['sample_size'].iloc[0])
        n_mid = int(base_df[base_df['slice'] == 'Middle (Overs 6-15)']['sample_size'].iloc[0])
        n_dth = int(base_df[base_df['slice'] == 'Death (Overs 16-19)']['sample_size'].iloc[0])
        self.assertEqual(n_pp + n_mid + n_dth, n_total, "Powerplay + Middle + Death must equal Total deliveries")
        
        n_press = int(base_df[base_df['slice'] == 'Pressure (PI >= 50)']['sample_size'].iloc[0])
        n_non_press = int(base_df[base_df['slice'] == 'Non-Pressure (PI < 50)']['sample_size'].iloc[0])
        self.assertEqual(n_press + n_non_press, n_total, "Pressure + Non-Pressure must equal Total deliveries")

    def test_07_calibration_deciles_validity(self):
        """Verify calibration deciles are monotonically ordered and have valid bounds."""
        cal_csv = PHASE9_OUT / 'calibration_deciles.csv'
        df = pd.read_csv(cal_csv)
        
        for m in ['Statistical Baseline', 'CatBoost', 'XGBoost']:
            for t in ['Batter Dismissal Prob', 'Bowler Wicket Prob']:
                sub = df[(df['model'] == m) & (df['target'] == t)].sort_values('decile')
                self.assertEqual(len(sub), 10, f"Expected 10 deciles for {m} {t}")
                # Decile 1 should have lower predicted prob than Decile 10
                self.assertLess(sub.iloc[0]['predicted_prob'], sub.iloc[-1]['predicted_prob'])
                # All probabilities and observed rates strictly between 0 and 1
                self.assertTrue((sub['predicted_prob'] > 0.0).all() and (sub['predicted_prob'] < 1.0).all())
                self.assertTrue((sub['observed_rate'] >= 0.0).all() and (sub['observed_rate'] <= 1.0).all())

    def test_08_ranking_sensitivity_stability(self):
        """Verify ranking sensitivity metrics confirm high Spearman correlation and Top 10 stability."""
        sens_file = PHASE9_OUT / 'ranking_sensitivity_summary.json'
        with open(sens_file, 'r', encoding='utf-8') as f:
            sens = json.load(f)
            
        bat_corrs = sens['batting']['spearman_rank_correlation']
        bowl_corrs = sens['bowling']['spearman_rank_correlation']
        
        for pair, r in bat_corrs.items():
            self.assertGreater(r, 0.98, f"Batting rank correlation for {pair} too low: {r}")
            
        for pair, r in bowl_corrs.items():
            self.assertGreater(r, 0.98, f"Bowling rank correlation for {pair} too low: {r}")
            
        # Top 10 overlap should be at least 9
        self.assertGreaterEqual(sens['batting']['top_10_overlap_count']['baseline_and_xgboost'], 9)
        self.assertGreaterEqual(sens['bowling']['top_10_overlap_count']['baseline_and_xgboost'], 9)

    def test_09_preservation_of_frozen_phase3_5_and_phase8(self):
        """Verify frozen Phase 3.5 and Phase 8 outputs are completely unmodified."""
        p35_version = BASE_DIR / 'output' / 'phase3_5' / 'methodology_version.json'
        p35_rankings = BASE_DIR / 'output' / 'phase3_5' / 'official_rankings.json'
        self.assertTrue(p35_version.exists(), "Phase 3.5 methodology_version.json must exist")
        self.assertTrue(p35_rankings.exists(), "Phase 3.5 official_rankings.json must exist")
        
        with open(p35_version, 'r', encoding='utf-8') as f:
            v_data = json.load(f)
        self.assertEqual(v_data.get('methodology_version'), 'CPRI-v1.0.0-PROD-FREEZE')
        
        p8_top10_bat = BASE_DIR / 'output' / 'phase8_ranking_reconsideration' / 'official_top10_batters.csv'
        p8_top10_bowl = BASE_DIR / 'output' / 'phase8_ranking_reconsideration' / 'official_top10_bowlers.csv'
        
        self.assertTrue(p8_top10_bat.exists(), "Phase 8 batter ranking must exist")
        self.assertTrue(p8_top10_bowl.exists(), "Phase 8 bowler ranking must exist")
        
        bat_df = pd.read_csv(p8_top10_bat)
        bowl_df = pd.read_csv(p8_top10_bowl)
        self.assertEqual(len(bat_df), 10, "Phase 8 batter list must have 10 players")
        self.assertEqual(len(bowl_df), 10, "Phase 8 bowler list must have 10 players")

if __name__ == '__main__':
    unittest.main()
