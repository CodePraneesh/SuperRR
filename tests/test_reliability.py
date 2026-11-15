# test_reliability.py
import unittest
import pandas as pd
import numpy as np
from ml.phase3.reliability import (
    apply_bayesian_shrinkage,
    calculate_reliability_confidence,
    assign_confidence_tier,
    min_max_normalize
)

class TestReliability(unittest.TestCase):
    def test_01_bayesian_shrinkage_direction(self):
        # Raw value higher than pop mean should shrink downwards
        raw = pd.Series([100.0, 50.0, 0.0])
        samples = pd.Series([10.0, 50.0, 10.0])
        shrunk = apply_bayesian_shrinkage(raw, samples, m_prior_weight=40.0)
        pop_mean = raw.mean() # 50.0
        self.assertLess(shrunk.iloc[0], raw.iloc[0])
        self.assertGreater(shrunk.iloc[2], raw.iloc[2])
        self.assertAlmostEqual(shrunk.iloc[1], 50.0)

    def test_02_reliability_confidence_bounds(self):
        samples = pd.Series([0, 10, 60, 150, 300, 1000])
        r = calculate_reliability_confidence(samples, n_threshold=150.0)
        self.assertTrue((r >= 0.0).all() and (r <= 100.0).all())
        self.assertAlmostEqual(r.iloc[0], 0.0)
        self.assertGreater(r.iloc[3], 60.0)
        self.assertGreater(r.iloc[5], 99.0)

    def test_03_confidence_tier_assignment(self):
        samples = pd.Series([30, 80, 200])
        tiers = assign_confidence_tier(samples, high_thresh=150, mod_thresh=60)
        self.assertEqual(tiers.tolist(), ['Low Confidence', 'Moderate Confidence', 'High Confidence'])

    def test_04_min_max_normalize(self):
        s = pd.Series([10.0, 20.0, 30.0])
        norm = min_max_normalize(s)
        self.assertAlmostEqual(norm.min(), 0.0)
        self.assertAlmostEqual(norm.max(), 100.0)
        self.assertAlmostEqual(norm.iloc[1], 50.0)

if __name__ == '__main__':
    unittest.main()
