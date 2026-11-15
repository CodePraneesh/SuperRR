# test_cpri_bowler.py
import unittest
import pandas as pd
from pathlib import Path
from ml.phase3.cpri_bowler import compute_bowler_cpri

BASE_DIR = Path(__file__).resolve().parent.parent

class TestCPRIBowler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bw_path = BASE_DIR / 'output' / 'phase2' / 'bowler_delivery_expectations.csv'
        w_path = BASE_DIR / 'output' / 'phase2' / 'delivery_wpa.csv'
        cls.bw_df = pd.read_csv(bw_path, nrows=5000)
        cls.w_df = pd.read_csv(w_path, nrows=5000)
        cls.bowlers, cls.matches = compute_bowler_cpri(cls.bw_df, cls.w_df)

    def test_01_cpri_score_bounds(self):
        self.assertTrue((self.bowlers['cpri_score'] >= 0.0).all())
        self.assertTrue((self.bowlers['cpri_score'] <= 100.0).all())

    def test_02_component_scores_bounds(self):
        for col in ['score_pressure_impact', 'score_adaptability', 'score_consistency', 'score_reliability']:
            self.assertTrue((self.bowlers[col] >= 0.0).all(), f'{col} has values < 0')
            self.assertTrue((self.bowlers[col] <= 100.0).all(), f'{col} has values > 100')

    def test_03_no_players_dropped(self):
        raw_pids = self.bw_df['bowler_id'].nunique()
        res_pids = self.bowlers['player_id'].nunique()
        self.assertEqual(raw_pids, res_pids)

    def test_04_ranks_monotonic(self):
        for scope, grp in self.bowlers.groupby('competition_scope'):
            self.assertTrue(grp['cpri_score'].is_monotonic_decreasing)

if __name__ == '__main__':
    unittest.main()
