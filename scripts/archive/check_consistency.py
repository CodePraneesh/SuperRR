import os
import pandas as pd
import numpy as np

os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')

b_df = pd.read_csv('output/phase2/batter_delivery_expectations.csv', low_memory=False)
bw_df = pd.read_csv('output/phase2/bowler_delivery_expectations.csv', low_memory=False)
wpa_df = pd.read_csv('output/phase2/delivery_wpa.csv', low_memory=False)

w_cols = ['match_id', 'innings', 'overid', 'over_ball_num', 'batting_wpa', 'bowling_wpa']
d = b_df.merge(wpa_df[w_cols], on=['match_id', 'innings', 'overid', 'over_ball_num'], how='left')
d['batting_wpa'] = d['batting_wpa'].fillna(0.0)
d['is_pressure'] = d['pressure_score'] >= 50.0

p_delivs = d[d['is_pressure']]

# Player-match pressure stats
p_match = p_delivs.groupby(['striker_id', 'competition_scope', 'match_id']).agg(
    p_balls=('actual_batter_runs', 'count'),
    run_res=('batting_run_residual', 'sum'),
    surv_res=('batting_dismissal_residual', 'sum'),
    wpa=('batting_wpa', 'sum')
).reset_index()

p_match['match_net_impact'] = p_match['run_res'] + 12.0 * p_match['surv_res'] + 25.0 * p_match['wpa']
p_match['match_net_impact_rate'] = (p_match['match_net_impact'] / p_match['p_balls']) * 100.0

consist_stats = p_match.groupby(['striker_id', 'competition_scope']).agg(
    p_matches=('match_id', 'nunique'),
    pos_match_ratio=('match_net_impact', lambda s: (s > 0).mean()),
    mean_match_residual=('match_net_impact', 'mean'),
    std_match_residual=('match_net_impact', lambda s: s.std(ddof=0) if len(s) > 1 else 10.0)
).reset_index()

print("Consistency stats sample:")
print(consist_stats.describe())
