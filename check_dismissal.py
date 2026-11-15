import os
import pandas as pd
os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')
df = pd.read_csv('output/phase2/batter_delivery_expectations.csv', nrows=10)
for i, r in df.iterrows():
    print(f"p_run_delta: {r['pressure_adjusted_batting_run_delta']:.4f} | p_out_delta: {r['pressure_adjusted_batting_out_delta']:.4f}")
