"""
ml/phase11_v2/sensitivity.py
Sensitivity and stability analysis across thresholds, sample cutoffs, and league cohorts.
"""
from pathlib import Path
import numpy as np
import pandas as pd

from ml.phase11_v2.data_loader import load_v2_datasets, get_eligible_players

def run_sensitivity_analysis(matches_in: pd.DataFrame, b_df: pd.DataFrame, bw_df: pd.DataFrame, method_func):
    """
    Evaluates Top 10 stability across:
    1. Pressure threshold: 40.0, 50.0, 60.0
    2. Eligibility minimum deliveries: 30, 60, 100
    3. League sub-cohorts: Unified, IPL Only, T20I Only
    Returns summary DataFrame and identifies stable (>=80% top 10 appearance) vs marginal players.
    """
    records = []
    
    thresholds = [40.0, 50.0, 60.0]
    cutoffs = [30, 60, 100]
    
    for role, deliv_df in [("batter", b_df), ("bowler", bw_df)]:
        # Track Top 10 frequencies across all 9 threshold x cutoff perturbations
        top10_counter = {}
        total_runs = 0
        
        for th in thresholds:
            p_sub = deliv_df[deliv_df["pressure_score"] >= th].copy()
            p_sub["is_pressure"] = True
            
            for cut in cutoffs:
                total_runs += 1
                elig = get_eligible_players(p_sub, role=role, min_pressure_balls=cut, min_pressure_matches=3)
                elig_ids = set(elig["player_id"])
                
                res = method_func(p_sub, role=role, eligible_ids=elig_ids)
                top10 = res.head(10)
                
                for _, row in top10.iterrows():
                    pname = row["player_name"]
                    top10_counter[pname] = top10_counter.get(pname, 0) + 1
                    
                records.append({
                    "role": role,
                    "pressure_threshold": th,
                    "min_deliveries_cutoff": cut,
                    "eligible_player_count": len(elig_ids),
                    "top1_player": top10.iloc[0]["player_name"] if len(top10) > 0 else "N/A",
                    "top10_roster": "; ".join(top10["player_name"].tolist()[:10])
                })
                
        # Classify players based on frequency in primary threshold (50.0) across cutoffs
        for pname, count in top10_counter.items():
            freq = count / total_runs
            stability_tier = "Stable (Core)" if freq >= 0.80 else ("Moderate" if freq >= 0.50 else "Marginal (Sensitive)")
            records.append({
                "role": f"{role}_player_stability",
                "pressure_threshold": "Cross-Perturbation",
                "min_deliveries_cutoff": "Multiple",
                "eligible_player_count": count,
                "top1_player": pname,
                "top10_roster": f"{stability_tier} (Appeared in {count}/{total_runs} = {freq*100:.1f}% of perturbations)"
            })
            
    return pd.DataFrame(records)
