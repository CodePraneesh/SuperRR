import os
import pandas as pd

os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')
df = pd.read_csv('output/phase3_1/phase3_1_coefficient_sensitivity.csv')
print(df.head(20))
print("\nSummary by parameter type:")
print(df.groupby(['parameter_type', 'role'])['spearman_rank_correlation'].agg(['min', 'mean', 'max']))
print("\nTop 10 overlap summary:")
print(df.groupby(['parameter_type', 'role'])['top10_overlap_count'].agg(['min', 'mean', 'max']))
