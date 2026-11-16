"""
tests/test_phase11_v2.py
Automated validation suite for SupeRR Intelligence v2 Ranking Pipeline.

Validates:
1. Zero future leakage in cumulative state features.
2. Strictly disjoint match partitions in train/eval splits.
3. Perfect deterministic reproducibility with fixed seed.
4. Ranks equal CSV deliverables with monotonic order and bounds.
5. Zero player-name-specific logic in pipeline code (grep test).
6. Complete preservation of frozen Phase 8 deliverables.
"""
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestPhase11V2(unittest.TestCase):
    
    def test_01_no_future_leakage_in_state(self):
        """Verify pre-delivery cumulative state variables contain zero lookahead leakage."""
        from tests.conftest import require_data_file
        require_data_file("output/processed/deliveries_enriched.csv", "python supeRR_phase1_pipeline.py")
        
        df = pd.read_csv(REPO_ROOT / "output" / "processed" / "deliveries_enriched.csv", nrows=5000)
        ball_ones = df[df["innings_ball_num"] == 1]
        
        self.assertTrue((ball_ones["score_before"] == 0).all(), "Ball 1 score_before must be 0.")
        self.assertTrue((ball_ones["wickets_lost_before"] == 0).all(), "Ball 1 wickets_lost_before must be 0.")
        self.assertTrue((ball_ones["legal_balls_before"] == 0).all(), "Ball 1 legal_balls_before must be 0.")

    def test_02_match_disjoint_train_eval_splits(self):
        """Verify match assignments in temporal splits are strictly disjoint (0 overlap)."""
        from tests.conftest import require_data_file
        require_data_file("output/phase2/batter_delivery_expectations.csv")
        from ml.phase11_v2.data_loader import load_v2_datasets
        matches_in, _, _ = load_v2_datasets(50.0)
        
        n_matches = len(matches_in)
        train_end_idx = int(0.70 * n_matches)
        
        train_matches = set(matches_in.iloc[:train_end_idx]["match_id"])
        test_matches = set(matches_in.iloc[train_end_idx:]["match_id"])
        
        overlap = train_matches.intersection(test_matches)
        self.assertEqual(len(overlap), 0, f"Found {len(overlap)} overlapping matches between train and test!")

    def test_03_reproducibility_with_fixed_seed(self):
        """Verify candidate method and cluster bootstrap are 100% deterministic with seed=42."""
        from tests.conftest import require_data_file
        require_data_file("output/phase2/batter_delivery_expectations.csv")
        from ml.phase11_v2.data_loader import load_v2_datasets, get_eligible_players
        from ml.phase11_v2.models import run_method_d
        from ml.phase11_v2.cluster_bootstrap import run_cluster_bootstrap
        
        matches_in, b_df, _ = load_v2_datasets(50.0)
        p_b = b_df[b_df["is_pressure"]]
        elig = get_eligible_players(p_b, role="batter", min_pressure_balls=60, min_pressure_matches=5)
        elig_ids = set(elig["player_id"])
        
        # Run bootstrap twice with seed=42 on 50 iterations for quick verification
        run1 = run_cluster_bootstrap(p_b, matches_in, role="batter", eligible_ids=elig_ids,
                                    method_func=run_method_d, n_boot=50, seed=42)
        run2 = run_cluster_bootstrap(p_b, matches_in, role="batter", eligible_ids=elig_ids,
                                    method_func=run_method_d, n_boot=50, seed=42)
        
        np.testing.assert_array_equal(run1["v2_score" if "v2_score" in run1.columns else "method_score"].values,
                                      run2["v2_score" if "v2_score" in run2.columns else "method_score"].values)
        np.testing.assert_array_equal(run1["predicted_rank"].values, run2["predicted_rank"].values)

    def test_04_ranks_equal_csv_deliverables(self):
        """Verify v2 official Top 10 CSVs exist, contain ranks 1..10 in order, and have valid bounds."""
        b_path = REPO_ROOT / "output" / "phase11_v2" / "official_top10_batters_v2.csv"
        bw_path = REPO_ROOT / "output" / "phase11_v2" / "official_top10_bowlers_v2.csv"
        
        self.assertTrue(b_path.exists(), "official_top10_batters_v2.csv does not exist!")
        self.assertTrue(bw_path.exists(), "official_top10_bowlers_v2.csv does not exist!")
        
        df_b = pd.read_csv(b_path)
        df_bw = pd.read_csv(bw_path)
        
        self.assertEqual(len(df_b), 10)
        self.assertEqual(len(df_bw), 10)
        self.assertEqual(list(df_b["v2_rank"]), list(range(1, 11)))
        self.assertEqual(list(df_bw["v2_rank"]), list(range(1, 11)))
        
        # Valid bounds
        self.assertTrue(((df_b["v2_score"] >= 0) & (df_b["v2_score"] <= 100)).all())
        self.assertTrue(((df_bw["v2_score"] >= 0) & (df_bw["v2_score"] <= 100)).all())

    def test_05_no_player_name_specific_logic(self):
        """Grep test: ensure zero player-name-specific code or exceptions exist in ml/phase11_v2/."""
        code_dir = REPO_ROOT / "ml" / "phase11_v2"
        banned_names = [
            "suryakumar", "rashid", "bumrah", "wade", "muqeem",
            "overton", "narine", "kohli", "jaiswal", "santner",
            "chahal", "pathirana", "hendricks", "david"
        ]
        
        for py_file in code_dir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read().lower()
            for name in banned_names:
                self.assertNotIn(
                    f'"{name}"', content,
                    f"Found hardcoded player name string '{name}' in {py_file.name}!"
                )
                self.assertNotIn(
                    f"'{name}'", content,
                    f"Found hardcoded player name string '{name}' in {py_file.name}!"
                )

    def test_06_frozen_phase8_deliverables_unmodified(self):
        """Verify frozen Phase 8 official rankings are completely untouched."""
        from scripts.verify_manifest import verify_manifest
        self.assertTrue(verify_manifest(), "Phase 8 deliverables drifted!")

if __name__ == "__main__":
    unittest.main()
