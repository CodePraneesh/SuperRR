import os
import sys
import unittest
from pathlib import Path

base_dir = str(Path(__file__).resolve().parent)
os.chdir(base_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

loader = unittest.TestLoader()

print("="*60)
print("RUNNING STANDALONE PHASE 1 TEST SUITE")
print("="*60)
p1_suite = loader.loadTestsFromName('test_phase1_validation')
p1_runner = unittest.TextTestRunner(verbosity=2)
p1_res = p1_runner.run(p1_suite)

print("\n" + "="*60)
print("RUNNING DISCOVERED TESTS (PHASE 2A, 2B, 2C, 3, 3.1)")
print("="*60)
disc_suite = loader.discover('tests', pattern='test_*.py')
disc_runner = unittest.TextTestRunner(verbosity=2)
disc_res = disc_runner.run(disc_suite)

success = p1_res.wasSuccessful() and disc_res.wasSuccessful()
print("\n" + "="*60)
print(f"OVERALL RESULT: {'ALL PASSED' if success else 'FAILED'}")
print(f"Phase 1 Tests: {p1_res.testsRun} run, {len(p1_res.failures)} failures, {len(p1_res.errors)} errors")
print(f"Phase 2/3/3.1 Tests: {disc_res.testsRun} run, {len(disc_res.failures)} failures, {len(disc_res.errors)} errors")
print(f"Total Combined Tests: {p1_res.testsRun + disc_res.testsRun}")
print("="*60)

sys.exit(0 if success else 1)
