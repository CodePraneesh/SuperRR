import os
import pandas as pd

os.chdir(r'C:\Users\Praneesh\OneDrive\Desktop\RR\SupeRR_Intelligence_Phase1\SupeRR_Phase1')

top_bat = pd.read_csv('output/phase3_1/top10_batters.csv')
top_bowl = pd.read_csv('output/phase3_1/top10_bowlers.csv')
ci = pd.read_csv('output/phase3_1/ranking_confidence_intervals.csv')

print("=== REFINED TOP 10 BATTERS (PHASE 3.1) ===")
for i, r in top_bat.iterrows():
    c = ci[(ci['player_id'] == r['player_id']) & (ci['competition_scope'] == r['competition_scope']) & (ci['role'] == 'Batter')]
    ci_str = f"[{c['ci_lower_95'].values[0]:.1f}, {c['ci_upper_95'].values[0]:.1f}]" if len(c) > 0 else "N/A"
    print(f"{r['competition_scope']} | #{r['official_rank']} {r['player_name']} | CPRI: {r['cpri_score']:.2f} | Imp: {r['score_pressure_impact']:.1f} | Adapt: {r['score_adaptability']:.1f} | Cons: {r['score_consistency']:.1f} | Rel: {r['score_reliability']:.1f} | PBalls: {r['pressure_deliveries']} | PMatches: {r['pressure_matches']} | TotBalls: {r['total_deliveries']} | Tier: {r['confidence_tier']} | 95% CI: {ci_str}")

print("\n=== REFINED TOP 10 BOWLERS (PHASE 3.1) ===")
for i, r in top_bowl.iterrows():
    c = ci[(ci['player_id'] == r['player_id']) & (ci['competition_scope'] == r['competition_scope']) & (ci['role'] == 'Bowler')]
    ci_str = f"[{c['ci_lower_95'].values[0]:.1f}, {c['ci_upper_95'].values[0]:.1f}]" if len(c) > 0 else "N/A"
    print(f"{r['competition_scope']} | #{r['official_rank']} {r['player_name']} | CPRI: {r['cpri_score']:.2f} | Imp: {r['score_pressure_impact']:.1f} | Adapt: {r['score_adaptability']:.1f} | Cons: {r['score_consistency']:.1f} | Rel: {r['score_reliability']:.1f} | PBalls: {r['pressure_deliveries']} | PMatches: {r['pressure_matches']} | TotBalls: {r['total_deliveries']} | Tier: {r['confidence_tier']} | 95% CI: {ci_str}")
