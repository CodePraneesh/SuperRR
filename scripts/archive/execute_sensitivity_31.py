import os
import sys

base_dir = r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1'
os.chdir(base_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from ml.phase3_1.sensitivity_analysis import run_coefficient_sensitivity_analysis

if __name__ == '__main__':
    run_coefficient_sensitivity_analysis()
