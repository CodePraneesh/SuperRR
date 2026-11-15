# test_ranking_engine.py
import unittest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class TestRankingEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top_bat = pd.read_csv(BASE_DIR / 'output' / 'phase3' / 'top10_batters.csv')
        cls.top_bowl = pd.read_csv(BASE_DIR / 'output' / 'phase3' / 'top10_bowlers.csv')
        cls.comp_df = pd.read_csv(BASE_DIR / 'output' / 'phase3' / 'cpri_component_scores.csv')
        cls.ci_df = pd.read_csv(BASE_DIR / 'output' / 'phase3' / 'ranking_confidence_intervals.csv')

    def test_01_top10_counts_and_scopes(self):
        for scope in ['IPL', 'T20I']:
            b_cnt = len(self.top_bat[self.top_bat['competition_scope'] == scope])
            bw_cnt = len(self.top_bowl[self.top_bowl['competition_scope'] == scope])
            self.assertEqual(b_cnt, 10, f'{scope} Top 10 batters count != 10')
            self.assertEqual(bw_cnt, 10, f'{scope} Top 10 bowlers count != 10')

    def test_02_top10_high_confidence_only(self):
        self.assertTrue((self.top_bat['confidence_tier'] == 'High Confidence').all())
        self.assertTrue((self.top_bowl['confidence_tier'] == 'High Confidence').all())
        self.assertTrue((self.top_bat['total_deliveries'] >= 150).all())
        self.assertTrue((self.top_bowl['total_deliveries'] >= 150).all())

    def test_03_component_weights_sum_to_cpri(self):
        # CPRI = 0.40 * Impact + 0.25 * Adapt + 0.20 * Consist + 0.15 * Rel
        calc_cpri = (
            0.40 * self.comp_df['score_pressure_impact'] +
            0.25 * self.comp_df['score_adaptability'] +
            0.20 * self.comp_df['score_consistency'] +
            0.15 * self.comp_df['score_reliability']
        ).round(2)
        diff = (self.comp_df['cpri_score'] - calc_cpri).abs()
        self.assertTrue((diff <= 0.05).all(), 'CPRI score deviates from weighted component sum!')

    def test_04_confidence_intervals_present(self):
        self.assertIn('ci_lower_95', self.ci_df.columns)
        self.assertIn('ci_upper_95', self.ci_df.columns)
        self.assertTrue((self.ci_df['ci_upper_95'] >= self.ci_df['ci_lower_95']).all())

if __name__ == '__main__':
    unittest.main()
