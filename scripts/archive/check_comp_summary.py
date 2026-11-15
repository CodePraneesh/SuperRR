import os
import pandas as pd
from scipy.stats import spearmanr

os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')

df_comp = pd.read_csv('output/phase3_1/phase3_1_ranking_comparison.csv')
p3_top_bat = pd.read_csv('output/phase3/top10_batters.csv')
p31_top_bat = pd.read_csv('output/phase3_1/top10_batters.csv')
p3_top_bowl = pd.read_csv('output/phase3/top10_bowlers.csv')
p31_top_bowl = pd.read_csv('output/phase3_1/top10_bowlers.csv')

print("=== RANKING COMPARISON SUMMARY ===")
for scope in ['IPL', 'T20I']:
    for role in ['Batter', 'Bowler']:
        sub = df_comp[(df_comp['competition_scope'] == scope) & (df_comp['role'] == role)]
        rho, _ = spearmanr(sub['p3_rank'], sub['p31_rank'])
        
        if role == 'Batter':
            t10_p3 = set(p3_top_bat[p3_top_bat['competition_scope'] == scope]['player_id'])
            t10_p31 = set(p31_top_bat[p31_top_bat['competition_scope'] == scope]['player_id'])
        else:
            t10_p3 = set(p3_top_bowl[p3_top_bowl['competition_scope'] == scope]['player_id'])
            t10_p31 = set(p31_top_bowl[p31_top_bowl['competition_scope'] == scope]['player_id'])
            
        overlap = len(t10_p3.intersection(t10_p31))
        print(f"{scope} {role} | Full Pop Spearman: {rho:.4f} | Top 10 Overlap: {overlap}/10")
