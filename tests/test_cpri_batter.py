# test_cpri_batter.py
import unittest
import pandas as pd
from pathlib import Path
from ml.phase3.cpri_batter import compute_batter_cpri

BASE_DIR = Path(__file__).resolve().parent.parent

class TestCPRIBatter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        b_path = BASE_DIR / 'output' / 'phase2' / 'batter_delivery_expectations.csv'
        w_path = BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv'
        cls.b_df = pd.read_csv(b_path, nrows=5000)
        cls.w_df = pd.read_csv(w_path, nrows=5000)
        cls.batters, cls.matches = compute_batter_cpri(cls.b_df, cls.w_df)

    def test_01_cpri_score_bounds(self):
        self.assertTrue((self.batters['cpri_score'] >= 0.0).all())
        self.assertTrue((self.batters['cpri_score'] <= 100.0).all())

    def test_02_component_scores_bounds(self):
        for col in ['score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability']:
            self.assertTrue((self.batters[col] >= 0.0).all(), f'{col} has values < 0')
            self.assertTrue((self.batters[col] <= 100.0).all(), f'{col} has values > 100')

    def test_03_no_players_dropped(self):
        raw_pids = self.b_df['striker_id'].nunique()
        res_pids = self.batters['player_id'].nunique()
        self.assertEqual(raw_pids, res_pids)

    def test_04_ranks_monotonic(self):
        for scope, grp in self.batters.groupby('competition_scope'):
            self.assertTrue(grp['cpri_score'].is_monotonic_decreasing)

if __name__ == '__main__':
    unittest.main()
