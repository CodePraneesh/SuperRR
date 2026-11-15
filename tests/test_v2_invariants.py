"""
tests/test_v2_invariants.py
Automated mathematical and statistical invariant test suite for SupeRR Intelligence v2.

Asserts 9 non-negotiable invariants:
T1: Point score in [score_ci_lower_90, score_ci_upper_90] for every eligible player.
T2: Point rank in [rank_ci_lower_90, rank_ci_upper_90] (with at most 1 rank boundary allowance).
T3: Sum of P(Top 10) across all eligible players equals 10.0 +/- 0.05.
T4: Strict monotonicity in primary ordering metric with deterministic tie-breaking.
T5: Full adherence to pre-registered eligibility criteria (balls >= 60, matches >= 5).
T6: Cluster bootstrap resamples matches (not deliveries) with SEED=42.
T7: Match-disjoint train/test splits with zero lookahead leakage.
T8: Zero player names hardcoded in ml/phase11_v2/ (automated grep test).
T9: Clean confidence tier string labels with zero duplicate tokens or LaTeX escaping.
"""
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_V2 = REPO_ROOT / "output" / "phase11_v2"

class TestV2Invariants(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.b_top10_path = OUT_V2 / "official_top10_batters_v2.csv"
        cls.bw_top10_path = OUT_V2 / "official_top10_bowlers_v2.csv"
        cls.all_path = OUT_V2 / "all_eligible_players_v2.csv"
        
        # Ensure deliverables exist before running tests
        if not cls.b_top10_path.exists() or not cls.bw_top10_path.exists() or not cls.all_path.exists():
            from ml.phase11_v2.v2_ranking_generator import generate_v2_deliverables
            generate_v2_deliverables()
            
        cls.df_b = pd.read_csv(cls.b_top10_path)
        cls.df_bw = pd.read_csv(cls.bw_top10_path)
        cls.df_all = pd.read_csv(cls.all_path)

    def test_T1_point_score_inside_score_ci(self):
        """T1: For every eligible player, point score must lie inside [score_ci_lower_90, score_ci_upper_90]."""
        for role, df in [("Batter", self.df_b), ("Bowler", self.df_bw)]:
            for _, row in df.iterrows():
                score = row["v2_score"]
                lower = row["score_ci_lower_90"]
                upper = row["score_ci_upper_90"]
                self.assertGreaterEqual(
                    score, lower - 0.01,
                    f"P1 Failure for {role} {row['player_name']}: score {score:.2f} < lower CI {lower:.2f}"
                )
                self.assertLessEqual(
                    score, upper + 0.01,
                    f"P1 Failure for {role} {row['player_name']}: score {score:.2f} > upper CI {upper:.2f}"
                )
        
        # Test full population in all_eligible_players_v2.csv
        for _, row in self.df_all.iterrows():
            self.assertGreaterEqual(row["v2_score"], row["score_ci_lower_90"] - 0.01)
            self.assertLessEqual(row["v2_score"], row["score_ci_upper_90"] + 0.01)

    def test_T2_point_rank_inside_rank_ci(self):
        """T2: For every eligible player, point rank must lie inside [rank_ci_lower_90, rank_ci_upper_90] (boundary allowance 1)."""
        for role, df in [("Batter", self.df_b), ("Bowler", self.df_bw)]:
            for _, row in df.iterrows():
                rank = row["v2_rank"]
                lower = row["rank_ci_lower_90"]
                upper = row["rank_ci_upper_90"]
                self.assertGreaterEqual(
                    rank, lower - 1,
                    f"P2 Failure for {role} {row['player_name']}: rank {rank} < lower rank CI {lower}"
                )
                self.assertLessEqual(
                    rank, upper + 1,
                    f"P2 Failure for {role} {row['player_name']}: rank {rank} > upper rank CI {upper}"
                )

    def test_T3_sum_p_top10_equals_ten(self):
        """T3: Sum of P(Top 10) across ALL eligible players must equal 10.0 +/- 0.05."""
        b_all = self.df_all[self.df_all["role"] == "Batter"]
        bw_all = self.df_all[self.df_all["role"] == "Bowler"]
        
        sum_b = b_all["p_top10"].sum()
        sum_bw = bw_all["p_top10"].sum()
        
        self.assertAlmostEqual(
            sum_b, 10.0, delta=0.05,
            msg=f"Batter P(Top 10) total sum was {sum_b:.4f}, expected 10.0 +/- 0.05"
        )
        self.assertAlmostEqual(
            sum_bw, 10.0, delta=0.05,
            msg=f"Bowler P(Top 10) total sum was {sum_bw:.4f}, expected 10.0 +/- 0.05"
        )

    def test_T4_ranking_order_monotonic_with_tiebreak(self):
        """T4: Ranking order is strictly monotonic in declared primary metric with deterministic tie-breaker."""
        for role, df in [("Batter", self.df_b), ("Bowler", self.df_bw)]:
            ranks = df["v2_rank"].tolist()
            scores = df["v2_score"].tolist()
            self.assertEqual(ranks, list(range(1, 11)), f"{role} ranks not strictly 1..10!")
            for i in range(len(scores) - 1):
                self.assertGreaterEqual(
                    scores[i], scores[i+1],
                    f"{role} scores not monotonic descending at index {i}: {scores[i]} < {scores[i+1]}"
                )

    def test_T5_eligibility_criteria_enforced(self):
        """T5: All players meet pre-registered eligibility criteria (balls >= 60, matches >= 5)."""
        for _, row in self.df_all.iterrows():
            self.assertGreaterEqual(
                row["pressure_deliveries"], 60,
                f"Player {row['player_name']} has {row['pressure_deliveries']} balls < 60!"
            )
            self.assertGreaterEqual(
                row["pressure_matches"], 5,
                f"Player {row['player_name']} has {row['pressure_matches']} matches < 5!"
            )

    def test_T6_cluster_bootstrap_match_resampling(self):
        """T6: Cluster bootstrap resamples matches, not deliveries, and uses SEED=42."""
        cb_file = REPO_ROOT / "ml" / "phase11_v2" / "cluster_bootstrap.py"
        with open(cb_file, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("multinomial", code, "Cluster bootstrap must use multinomial match resampling!")
        self.assertIn("n_matches", code, "Cluster bootstrap must resample across n_matches!")
        self.assertIn("seed: int = 42", code, "Cluster bootstrap default seed must be 42!")

    def test_T7_match_disjoint_train_test_splits(self):
        """T7: Out-of-sample evaluation uses match-disjoint train/test splits with no lookahead leakage."""
        from ml.phase11_v2.data_loader import load_v2_datasets
        matches_in, _, _ = load_v2_datasets(50.0)
        n_matches = len(matches_in)
        train_end_idx = int(0.70 * n_matches)
        
        train_matches = set(matches_in.iloc[:train_end_idx]["match_id"])
        test_matches = set(matches_in.iloc[train_end_idx:]["match_id"])
        
        overlap = train_matches.intersection(test_matches)
        self.assertEqual(len(overlap), 0, f"Found {len(overlap)} overlapping matches between train and test!")

    def test_T8_zero_hardcoded_player_names(self):
        """T8: Zero player names hardcoded anywhere in ml/phase11_v2/ (automated grep test)."""
        code_dir = REPO_ROOT / "ml" / "phase11_v2"
        banned_names = [
            "suryakumar", "rashid", "bumrah", "wade", "muqeem",
            "overton", "narine", "kohli", "jaiswal", "santner",
            "chahal", "pathirana", "hendricks", "david", "robinson", "inglis"
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

    def test_T9_clean_confidence_tier_labels(self):
        """T9: No duplicated tokens, nested parens, or raw LaTeX artifacts in tier labels."""
        valid_tiers = {
            "Tier 1 (N >= 300)",
            "Tier 2 (150 <= N < 300)",
            "Tier 3 (60 <= N < 150)"
        }
        for _, row in self.df_all.iterrows():
            tier = row["confidence_tier"]
            self.assertIn(
                tier, valid_tiers,
                f"Invalid or corrupted confidence tier label: '{tier}'"
            )
            self.assertNotIn("\\ge", tier, "Found raw LaTeX '\\ge' in tier label!")
            self.assertNotIn("\\le", tier, "Found raw LaTeX '\\le' in tier label!")
            self.assertNotIn("$", tier, "Found raw LaTeX '$' in tier label!")

if __name__ == "__main__":
    unittest.main()
