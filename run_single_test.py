import os
import sys
import unittest
from pathlib import Path

base_dir = str(Path(__file__).resolve().parent)
os.chdir(base_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

loader = unittest.TestLoader()
suite = loader.discover('tests', pattern='test_cpri_31.py')
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
