import os
import pandas as pd
import numpy as np

os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')

b_df = pd.read_csv('output/phase2/batter_delivery_expectations.csv', low_memory=False)
bw_df = pd.read_csv('output/phase2/bowler_delivery_expectations.csv', low_memory=False)

b_df['is_pressure'] = b_df['pressure_score'] >= 50.0
bw_df['is_pressure'] = bw_df['pressure_score'] >= 50.0

b_stats = b_df.groupby(['striker_id', 'competition_scope']).agg(
    total_balls=('actual_batter_runs', 'count'),
    p_balls=('is_pressure', 'sum'),
    p_matches=('match_id', lambda m: b_df.loc[m.index, 'match_id'][b_df.loc[m.index, 'is_pressure']].nunique())
).reset_index()

print("Batters meeting criteria:")
print("total_balls >= 150:", (b_stats['total_balls'] >= 150).sum())
print("p_balls >= 50:", (b_stats['p_balls'] >= 50).sum())
print("p_balls >= 50 and p_matches >= 3:", ((b_stats['p_balls'] >= 50) & (b_stats['p_matches'] >= 3)).sum())
print("total_balls >= 150 and p_balls >= 50 and p_matches >= 3:", ((b_stats['total_balls'] >= 150) & (b_stats['p_balls'] >= 50) & (b_stats['p_matches'] >= 3)).sum())
