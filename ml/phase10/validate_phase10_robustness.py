#!/usr/bin/env python3
"""
validate_phase10_robustness.py
Phase 10: Final CPRI Top 10 Contextual Validation and Robustness Engine.
Evaluates the credibility, fairness, and robustness of the official Phase 8
Top 10 batter and bowler rankings (and Candidates 11-15) across:
  1. Format robustness (IPL vs T20I vs Dual)
  2. Innings-phase robustness (Powerplay vs Middle vs Death)
  3. Pressure-level robustness (High vs Medium vs Low)
  4. Opposition-strength robustness (Leakage-safe historical win-rates)
  5. Sample reliability & coverage depth
  6. Cutoff stability (Ranks 8 to 15 comparison)
  7. Bootstrap rank uncertainty & Top 10 retention probability
Strictly preserves CPRI-v1.0.0-PROD-FREEZE and official Phase 8 CSVs.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PHASE2_DIR = BASE_DIR / 'output' / 'phase2'
PHASE8_DIR = BASE_DIR / 'output' / 'phase8_ranking_reconsideration'
OUT_DIR = BASE_DIR / 'output' / 'phase10_ranking_validation'

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 80)
    print("PHASE 10: FINAL CPRI TOP 10 VALIDATION & CONTEXTUAL ROBUSTNESS")
    print("=" * 80)
    
    # 1. LOAD CANDIDATES (Ranks 1 to 15)
    print("Loading official candidates (Ranks 1 to 15)...")
    bat_full = pd.read_csv(PHASE8_DIR / 'batter_full_population.csv')
    bowl_full = pd.read_csv(PHASE8_DIR / 'bowler_full_population.csv')
    
    bat_candidates = bat_full[(bat_full['official_rank'] >= 1) & (bat_full['official_rank'] <= 15)].sort_values('official_rank').copy()
    bowl_candidates = bowl_full[(bowl_full['official_rank'] >= 1) & (bowl_full['official_rank'] <= 15)].sort_values('official_rank').copy()
    
    bat_ids = set(bat_candidates['player_id'])
    bowl_ids = set(bowl_candidates['player_id'])
    
    print(f"Loaded {len(bat_candidates)} Batters and {len(bowl_candidates)} Bowlers.")

    # 2. LOAD DELIVERY-LEVEL DATASETS
    print("Loading frozen delivery expectations and matches...")
    bat_exp = pd.read_csv(PHASE2_DIR / 'batter_delivery_expectations.csv', low_memory=False)
    bowl_exp = pd.read_csv(PHASE2_DIR / 'bowler_delivery_expectations.csv', low_memory=False)
    matches = pd.read_csv(BASE_DIR / 'output' / 'processed' / 'matches_enriched.csv', low_memory=False)
    
    # Filter to active non-abandoned matches
    abandoned_ids = set(matches[matches.result.str.contains('Abandon|No result', case=False, na=False)]['match_id'])
    bat_exp = bat_exp[~bat_exp['match_id'].isin(abandoned_ids)].copy()
    bowl_exp = bowl_exp[~bowl_exp['match_id'].isin(abandoned_ids)].copy()
    
    bat_exp['match_date'] = pd.to_datetime(bat_exp['match_date'])
    bowl_exp['match_date'] = pd.to_datetime(bowl_exp['match_date'])
    
    # Filter deliveries for candidates
    cand_bat_delivs = bat_exp[bat_exp['striker_id'].isin(bat_ids)].copy()
    cand_bowl_delivs = bowl_exp[bowl_exp['bowler_id'].isin(bowl_ids)].copy()
    
    # 3. OPPOSITION STRENGTH PRE-CALCULATION (Leakage-Safe)
    print("Computing pre-match historical team win-rates for opposition strength...")
    matches['match_date_dt'] = pd.to_datetime(matches['match_date'])
    valid_matches = matches[~matches['match_id'].isin(abandoned_ids)].sort_values('match_date_dt').copy()
    
    # Precompute team win rates strictly before each match_date
    team_history = {}
    match_opp_strength = {} # (match_id, team_name) -> win_rate_before
    
    for _, m in valid_matches.iterrows():
        mid = m['match_id']
        t_home = m['home_team']
        t_away = m['away_team']
        w_team = m['win_team_id']
        
        # Calculate win rate before this match
        for t, tid in [(t_home, m['home_team_id']), (t_away, m['away_team_id'])]:
            hist = team_history.get(t, {'played': 0, 'won': 0})
            if hist['played'] >= 4:
                wr = hist['won'] / hist['played']
            else:
                # Bayesian prior shrinkage to 0.50 for early tournament / small samples
                wr = (hist['won'] + 2.0) / (hist['played'] + 4.0)
            match_opp_strength[(mid, t)] = wr
            
        # Update history after this match
        winner = m.get('winner', '')
        for t, tid in [(t_home, m['home_team_id']), (t_away, m['away_team_id'])]:
            if t not in team_history:
                team_history[t] = {'played': 0, 'won': 0}
            team_history[t]['played'] += 1
            if tid == w_team or (pd.notna(winner) and winner == t):
                team_history[t]['won'] += 1

    def get_opp_strength(row, is_batting=True):
        mid = row['match_id']
        # If batter is batting, opposition is bowling team
        opp_team = row['bowling_team_name_clean'] if is_batting else row['batting_team_name_clean']
        return match_opp_strength.get((mid, opp_team), 0.50)

    cand_bat_delivs['opp_win_rate'] = cand_bat_delivs.apply(lambda r: get_opp_strength(r, is_batting=True), axis=1)
    cand_bowl_delivs['opp_win_rate'] = cand_bowl_delivs.apply(lambda r: get_opp_strength(r, is_batting=False), axis=1)
    
    def assign_opp_tier(wr):
        if wr >= 0.55:
            return 'Top Tier (>=55%)'
        elif wr >= 0.45:
            return 'Balanced Tier (45-55%)'
        else:
            return 'Lower Tier (<45%)'
            
    cand_bat_delivs['opp_tier'] = cand_bat_delivs['opp_win_rate'].apply(assign_opp_tier)
    cand_bowl_delivs['opp_tier'] = cand_bowl_delivs['opp_win_rate'].apply(assign_opp_tier)

    # =========================================================================
    # DELIVERABLE 2: FORMAT ROBUSTNESS
    # =========================================================================
    print("Generating Deliverable 2: Format Robustness...")
    format_rows = []
    
    # Batters
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        p_evid = p['competition_evidence']
        cpri = p['cpri_score']
        
        p_delivs = cand_bat_delivs[cand_bat_delivs['striker_id'] == pid]
        p_press = p_delivs[p_delivs['pressure_score'] >= 50.0]
        
        # IPL
        ipl_press = p_press[p_press['competition_scope'] == 'IPL']
        ipl_balls = len(ipl_press)
        ipl_matches = ipl_press['match_id'].nunique()
        ipl_runs = ipl_press['actual_batter_runs'].sum() if ipl_balls > 0 else 0
        ipl_sr = (ipl_runs / ipl_balls * 100) if ipl_balls > 0 else np.nan
        ipl_run_res = ipl_press['batting_run_residual'].sum() if ipl_balls > 0 else 0.0
        ipl_out_res = ipl_press['batting_dismissal_residual'].sum() if ipl_balls > 0 else 0.0
        
        # T20I
        t20i_press = p_press[p_press['competition_scope'] == 'T20I']
        t20i_balls = len(t20i_press)
        t20i_matches = t20i_press['match_id'].nunique()
        t20i_runs = t20i_press['actual_batter_runs'].sum() if t20i_balls > 0 else 0
        t20i_sr = (t20i_runs / t20i_balls * 100) if t20i_balls > 0 else np.nan
        t20i_run_res = t20i_press['batting_run_residual'].sum() if t20i_balls > 0 else 0.0
        t20i_out_res = t20i_press['batting_dismissal_residual'].sum() if t20i_balls > 0 else 0.0
        
        # Format bias assessment
        if p_evid == 'Dual-Format':
            if ipl_balls >= 100 and t20i_balls >= 100:
                bias = 'Balanced Dual-Format (Extensive sample in both)'
            elif ipl_balls >= 100:
                bias = 'Dual-Format (IPL Primary, T20I Secondary)'
            else:
                bias = 'Dual-Format (T20I Primary, IPL Secondary)'
        elif p_evid == 'IPL-Only':
            bias = 'IPL-Exclusive Specialist'
        else:
            bias = 'T20I-Exclusive Specialist'
            
        format_rows.append({
            'role': 'Batter',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p_name,
            'competition_evidence': p_evid,
            'overall_cpri': cpri,
            'ipl_pressure_balls': ipl_balls,
            'ipl_pressure_matches': ipl_matches,
            'ipl_strike_rate': round(ipl_sr, 2) if pd.notna(ipl_sr) else np.nan,
            'ipl_run_residual': round(ipl_run_res, 2),
            'ipl_out_residual': round(ipl_out_res, 2),
            't20i_pressure_balls': t20i_balls,
            't20i_pressure_matches': t20i_matches,
            't20i_strike_rate': round(t20i_sr, 2) if pd.notna(t20i_sr) else np.nan,
            't20i_run_residual': round(t20i_run_res, 2),
            't20i_out_residual': round(t20i_out_res, 2),
            'format_assessment': bias
        })
        
    # Bowlers
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        p_evid = p['competition_evidence']
        cpri = p['cpri_score']
        
        p_delivs = cand_bowl_delivs[cand_bowl_delivs['bowler_id'] == pid]
        p_press = p_delivs[p_delivs['pressure_score'] >= 50.0]
        
        # IPL
        ipl_press = p_press[p_press['competition_scope'] == 'IPL']
        ipl_balls = len(ipl_press)
        ipl_matches = ipl_press['match_id'].nunique()
        ipl_runs = ipl_press['actual_runs_conceded'].sum() if ipl_balls > 0 else 0
        ipl_econ = (ipl_runs / (ipl_balls / 6.0)) if ipl_balls > 0 else np.nan
        ipl_run_saved = ipl_press['bowling_run_residual'].sum() if ipl_balls > 0 else 0.0
        ipl_wkt_res = ipl_press['bowling_wicket_residual'].sum() if ipl_balls > 0 else 0.0
        
        # T20I
        t20i_press = p_press[p_press['competition_scope'] == 'T20I']
        t20i_balls = len(t20i_press)
        t20i_matches = t20i_press['match_id'].nunique()
        t20i_runs = t20i_press['actual_runs_conceded'].sum() if t20i_balls > 0 else 0
        t20i_econ = (t20i_runs / (t20i_balls / 6.0)) if t20i_balls > 0 else np.nan
        t20i_run_saved = t20i_press['bowling_run_residual'].sum() if t20i_balls > 0 else 0.0
        t20i_wkt_res = t20i_press['bowling_wicket_residual'].sum() if t20i_balls > 0 else 0.0
        
        if p_evid == 'Dual-Format':
            if ipl_balls >= 100 and t20i_balls >= 100:
                bias = 'Balanced Dual-Format (Extensive sample in both)'
            elif ipl_balls >= 100:
                bias = 'Dual-Format (IPL Primary, T20I Secondary)'
            else:
                bias = 'Dual-Format (T20I Primary, IPL Secondary)'
        elif p_evid == 'IPL-Only':
            bias = 'IPL-Exclusive Specialist'
        else:
            bias = 'T20I-Exclusive Specialist'
            
        format_rows.append({
            'role': 'Bowler',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p_name,
            'competition_evidence': p_evid,
            'overall_cpri': cpri,
            'ipl_pressure_balls': ipl_balls,
            'ipl_pressure_matches': ipl_matches,
            'ipl_economy': round(ipl_econ, 2) if pd.notna(ipl_econ) else np.nan,
            'ipl_runs_saved': round(ipl_run_saved, 2),
            'ipl_wkts_above_exp': round(ipl_wkt_res, 2),
            't20i_pressure_balls': t20i_balls,
            't20i_pressure_matches': t20i_matches,
            't20i_economy': round(t20i_econ, 2) if pd.notna(t20i_econ) else np.nan,
            't20i_runs_saved': round(t20i_run_saved, 2),
            't20i_wkts_above_exp': round(t20i_wkt_res, 2),
            'format_assessment': bias
        })
        
    df_format = pd.DataFrame(format_rows)
    df_format.to_csv(OUT_DIR / 'phase10_format_robustness.csv', index=False)
    print("Saved phase10_format_robustness.csv")

    # =========================================================================
    # DELIVERABLE 3: INNINGS-PHASE ROBUSTNESS
    # =========================================================================
    print("Generating Deliverable 3: Innings-Phase Robustness...")
    phase_rows = []
    
    # Batters
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_press = cand_bat_delivs[(cand_bat_delivs['striker_id'] == pid) & (cand_bat_delivs['pressure_score'] >= 50.0)]
        
        for phase_name in ['Powerplay', 'Middle', 'Death']:
            sub = p_press[p_press['innings_phase'].str.lower() == phase_name.lower()]
            balls = len(sub)
            if balls > 0:
                act_runs = sub['actual_batter_runs'].sum()
                exp_runs = sub['expected_batter_runs'].sum()
                run_res = sub['batting_run_residual'].sum()
                outs = sub['actual_dismissal_outcome'].sum()
                exp_outs = sub['expected_dismissal_prob'].sum()
                out_res = sub['batting_dismissal_residual'].sum()
                sr = (act_runs / balls) * 100.0
            else:
                act_runs = exp_runs = run_res = outs = exp_outs = out_res = 0.0
                sr = np.nan
                
            phase_rows.append({
                'role': 'Batter',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'phase': phase_name,
                'phase_pressure_balls': balls,
                'actual_runs': int(act_runs),
                'expected_runs': round(exp_runs, 2),
                'run_residual': round(run_res, 2),
                'actual_outs': int(outs),
                'expected_outs': round(exp_outs, 2),
                'survival_residual': round(out_res, 2),
                'strike_rate': round(sr, 2) if pd.notna(sr) else np.nan
            })
            
    # Bowlers
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_press = cand_bowl_delivs[(cand_bowl_delivs['bowler_id'] == pid) & (cand_bowl_delivs['pressure_score'] >= 50.0)]
        
        for phase_name in ['Powerplay', 'Middle', 'Death']:
            sub = p_press[p_press['innings_phase'].str.lower() == phase_name.lower()]
            balls = len(sub)
            if balls > 0:
                act_runs = sub['actual_runs_conceded'].sum()
                exp_runs = sub['expected_runs_conceded'].sum()
                run_saved = sub['bowling_run_residual'].sum()
                wkts = sub['actual_wicket_outcome'].sum()
                exp_wkts = sub['expected_wicket_prob'].sum()
                wkt_res = sub['bowling_wicket_residual'].sum()
                econ = (act_runs / (balls / 6.0))
            else:
                act_runs = exp_runs = run_saved = wkts = exp_wkts = wkt_res = 0.0
                econ = np.nan
                
            phase_rows.append({
                'role': 'Bowler',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'phase': phase_name,
                'phase_pressure_balls': balls,
                'actual_runs_conceded': int(act_runs),
                'expected_runs_conceded': round(exp_runs, 2),
                'runs_saved': round(run_saved, 2),
                'actual_wkts': int(wkts),
                'expected_wkts': round(exp_wkts, 2),
                'wkts_above_exp': round(wkt_res, 2),
                'economy': round(econ, 2) if pd.notna(econ) else np.nan
            })
            
    df_phase = pd.DataFrame(phase_rows)
    df_phase.to_csv(OUT_DIR / 'phase10_innings_phase_robustness.csv', index=False)
    print("Saved phase10_innings_phase_robustness.csv")

    # =========================================================================
    # DELIVERABLE 4: PRESSURE-LEVEL ROBUSTNESS
    # =========================================================================
    print("Generating Deliverable 4: Pressure-Level Robustness...")
    pressure_rows = []
    
    # Batters
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_delivs = cand_bat_delivs[cand_bat_delivs['striker_id'] == pid]
        
        for tier_name, (pi_min, pi_max) in [('Low Pressure (PI < 25)', (0.0, 25.0)),
                                             ('Medium Pressure (25 <= PI < 50)', (25.0, 50.0)),
                                             ('High Pressure (PI >= 50)', (50.0, 100.0))]:
            sub = p_delivs[(p_delivs['pressure_score'] >= pi_min) & (p_delivs['pressure_score'] < pi_max if pi_max < 100.0 else p_delivs['pressure_score'] <= 100.0)]
            balls = len(sub)
            if balls > 0:
                act_runs = sub['actual_batter_runs'].sum()
                run_res = sub['batting_run_residual'].sum()
                res_per_ball = run_res / balls
                sr = (act_runs / balls) * 100.0
            else:
                run_res = res_per_ball = 0.0
                sr = np.nan
                
            pressure_rows.append({
                'role': 'Batter',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'pressure_tier': tier_name,
                'tier_balls': balls,
                'run_residual_total': round(run_res, 2),
                'run_residual_per_ball': round(res_per_ball, 4),
                'strike_rate': round(sr, 2) if pd.notna(sr) else np.nan
            })
            
    # Bowlers
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_delivs = cand_bowl_delivs[cand_bowl_delivs['bowler_id'] == pid]
        
        for tier_name, (pi_min, pi_max) in [('Low Pressure (PI < 25)', (0.0, 25.0)),
                                             ('Medium Pressure (25 <= PI < 50)', (25.0, 50.0)),
                                             ('High Pressure (PI >= 50)', (50.0, 100.0))]:
            sub = p_delivs[(p_delivs['pressure_score'] >= pi_min) & (p_delivs['pressure_score'] < pi_max if pi_max < 100.0 else p_delivs['pressure_score'] <= 100.0)]
            balls = len(sub)
            if balls > 0:
                act_runs = sub['actual_runs_conceded'].sum()
                run_saved = sub['bowling_run_residual'].sum()
                saved_per_ball = run_saved / balls
                econ = (act_runs / (balls / 6.0))
            else:
                run_saved = saved_per_ball = 0.0
                econ = np.nan
                
            pressure_rows.append({
                'role': 'Bowler',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'pressure_tier': tier_name,
                'tier_balls': balls,
                'runs_saved_total': round(run_saved, 2),
                'runs_saved_per_ball': round(saved_per_ball, 4),
                'economy': round(econ, 2) if pd.notna(econ) else np.nan
            })
            
    df_press = pd.DataFrame(pressure_rows)
    df_press.to_csv(OUT_DIR / 'phase10_pressure_robustness.csv', index=False)
    print("Saved phase10_pressure_robustness.csv")

    # =========================================================================
    # DELIVERABLE 5: OPPOSITION-STRENGTH ROBUSTNESS
    # =========================================================================
    print("Generating Deliverable 5: Opposition-Strength Robustness...")
    opp_rows = []
    
    # Batters
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_press = cand_bat_delivs[(cand_bat_delivs['striker_id'] == pid) & (cand_bat_delivs['pressure_score'] >= 50.0)]
        
        for tier in ['Top Tier (>=55%)', 'Balanced Tier (45-55%)', 'Lower Tier (<45%)']:
            sub = p_press[p_press['opp_tier'] == tier]
            balls = len(sub)
            if balls > 0:
                res = sub['batting_run_residual'].sum()
                sr = (sub['actual_batter_runs'].sum() / balls) * 100.0
                res_pb = res / balls
            else:
                res = res_pb = 0.0
                sr = np.nan
                
            opp_rows.append({
                'role': 'Batter',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'opposition_tier': tier,
                'pressure_balls': balls,
                'strike_rate': round(sr, 2) if pd.notna(sr) else np.nan,
                'run_residual': round(res, 2),
                'residual_per_ball': round(res_pb, 4)
            })
            
    # Bowlers
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_name = p['player_name']
        p_rank = int(p['official_rank'])
        
        p_press = cand_bowl_delivs[(cand_bowl_delivs['bowler_id'] == pid) & (cand_bowl_delivs['pressure_score'] >= 50.0)]
        
        for tier in ['Top Tier (>=55%)', 'Balanced Tier (45-55%)', 'Lower Tier (<45%)']:
            sub = p_press[p_press['opp_tier'] == tier]
            balls = len(sub)
            if balls > 0:
                saved = sub['bowling_run_residual'].sum()
                econ = (sub['actual_runs_conceded'].sum() / (balls / 6.0))
                saved_pb = saved / balls
            else:
                saved = saved_pb = 0.0
                econ = np.nan
                
            opp_rows.append({
                'role': 'Bowler',
                'official_rank': p_rank,
                'player_id': pid,
                'player_name': p_name,
                'opposition_tier': tier,
                'pressure_balls': balls,
                'economy': round(econ, 2) if pd.notna(econ) else np.nan,
                'runs_saved': round(saved, 2),
                'residual_per_ball': round(saved_pb, 4)
            })
            
    df_opp = pd.DataFrame(opp_rows)
    df_opp.to_csv(OUT_DIR / 'phase10_opposition_robustness.csv', index=False)
    print("Saved phase10_opposition_robustness.csv")

    # =========================================================================
    # DELIVERABLE 6: SAMPLE RELIABILITY & BREADTH
    # =========================================================================
    print("Generating Deliverable 6: Sample Reliability...")
    sample_rows = []
    
    # Batters
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_delivs = cand_bat_delivs[cand_bat_delivs['striker_id'] == pid]
        p_press = p_delivs[p_delivs['pressure_score'] >= 50.0]
        
        tot_balls = len(p_delivs)
        press_balls = len(p_press)
        press_matches = p_press['match_id'].nunique()
        opponents = p_press['bowling_team_name_clean'].nunique()
        seasons = p_press['match_date'].dt.year.nunique()
        
        phases = set(p_press['innings_phase'].unique())
        phase_cov = f"{len(phases)}/3 Phases ({', '.join(sorted(list(phases)))})"
        
        if press_balls >= 500:
            depth_tier = 'Very High Depth (>=500 balls)'
        elif press_balls >= 300:
            depth_tier = 'High Depth (300-499 balls)'
        elif press_balls >= 150:
            depth_tier = 'Moderate Depth (150-299 balls)'
        else:
            depth_tier = 'Borderline Depth (<150 balls)'
            
        sample_rows.append({
            'role': 'Batter',
            'official_rank': int(p['official_rank']),
            'player_id': pid,
            'player_name': p['player_name'],
            'competition_evidence': p['competition_evidence'],
            'total_deliveries': tot_balls,
            'pressure_deliveries': press_balls,
            'pressure_matches': press_matches,
            'distinct_opponents_faced': opponents,
            'distinct_seasons_active': seasons,
            'innings_phase_coverage': phase_cov,
            'sample_depth_tier': depth_tier
        })
        
    # Bowlers
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_delivs = cand_bowl_delivs[cand_bowl_delivs['bowler_id'] == pid]
        p_press = p_delivs[p_delivs['pressure_score'] >= 50.0]
        
        tot_balls = len(p_delivs)
        press_balls = len(p_press)
        press_matches = p_press['match_id'].nunique()
        opponents = p_press['batting_team_name_clean'].nunique()
        seasons = p_press['match_date'].dt.year.nunique()
        
        phases = set(p_press['innings_phase'].unique())
        phase_cov = f"{len(phases)}/3 Phases ({', '.join(sorted(list(phases)))})"
        
        if press_balls >= 500:
            depth_tier = 'Very High Depth (>=500 balls)'
        elif press_balls >= 300:
            depth_tier = 'High Depth (300-499 balls)'
        elif press_balls >= 150:
            depth_tier = 'Moderate Depth (150-299 balls)'
        else:
            depth_tier = 'Borderline Depth (<150 balls)'
            
        sample_rows.append({
            'role': 'Bowler',
            'official_rank': int(p['official_rank']),
            'player_id': pid,
            'player_name': p['player_name'],
            'competition_evidence': p['competition_evidence'],
            'total_deliveries': tot_balls,
            'pressure_deliveries': press_balls,
            'pressure_matches': press_matches,
            'distinct_opponents_faced': opponents,
            'distinct_seasons_active': seasons,
            'innings_phase_coverage': phase_cov,
            'sample_depth_tier': depth_tier
        })
        
    df_sample = pd.DataFrame(sample_rows)
    df_sample.to_csv(OUT_DIR / 'phase10_sample_reliability.csv', index=False)
    print("Saved phase10_sample_reliability.csv")

    # =========================================================================
    # DELIVERABLE 7: CUTOFF ANALYSIS (RANKS 8 TO 15)
    # =========================================================================
    print("Generating Deliverable 7: Cutoff Analysis (Ranks 8 to 15)...")
    cutoff_rows = []
    
    # Batters 8 to 15
    bat_rank10_cpri = float(bat_candidates[bat_candidates['official_rank'] == 10]['cpri_score'].iloc[0])
    bat_unc = pd.read_csv(PHASE8_DIR / 'batter_rank_uncertainty.csv').set_index('player_id')
    
    for _, p in bat_candidates[bat_candidates['official_rank'] >= 8].iterrows():
        pid = p['player_id']
        p_rank = int(p['official_rank'])
        cpri = p['cpri_score']
        margin = cpri - bat_rank10_cpri
        
        unc_row = bat_unc.loc[pid] if pid in bat_unc.index else None
        inc_prob = unc_row['top10_inclusion_freq'] if unc_row is not None else np.nan
        med_rank = unc_row['median_rank'] if unc_row is not None else np.nan
        
        if p_rank <= 10:
            verdict = 'Official Top 10 Qualifier'
        else:
            verdict = 'Contender Outside Cutoff'
            
        cutoff_rows.append({
            'role': 'Batter',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p['player_name'],
            'cpri_score': cpri,
            'margin_to_rank10': round(margin, 2),
            'pressure_deliveries': int(p['pressure_deliveries']),
            'pressure_matches': int(p['pressure_matches']),
            'pressure_strike_rate': p['pressure_strike_rate'],
            'pressure_run_res': p['pressure_run_res'],
            'top10_inclusion_freq': inc_prob,
            'median_resampled_rank': med_rank,
            'cutoff_status': verdict
        })
        
    # Bowlers 8 to 15
    bowl_rank10_cpri = float(bowl_candidates[bowl_candidates['official_rank'] == 10]['cpri_score'].iloc[0])
    bowl_unc = pd.read_csv(PHASE8_DIR / 'bowler_rank_uncertainty.csv').set_index('player_id')
    
    for _, p in bowl_candidates[bowl_candidates['official_rank'] >= 8].iterrows():
        pid = p['player_id']
        p_rank = int(p['official_rank'])
        cpri = p['cpri_score']
        margin = cpri - bowl_rank10_cpri
        
        unc_row = bowl_unc.loc[pid] if pid in bowl_unc.index else None
        inc_prob = unc_row['top10_inclusion_freq'] if unc_row is not None else np.nan
        med_rank = unc_row['median_rank'] if unc_row is not None else np.nan
        
        if p_rank <= 10:
            verdict = 'Official Top 10 Qualifier'
        else:
            verdict = 'Contender Outside Cutoff'
            
        cutoff_rows.append({
            'role': 'Bowler',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p['player_name'],
            'cpri_score': cpri,
            'margin_to_rank10': round(margin, 2),
            'pressure_deliveries': int(p['pressure_deliveries']),
            'pressure_matches': int(p['pressure_matches']),
            'pressure_economy': p['pressure_economy'],
            'pressure_wkts_above_exp': p['pressure_wkts_above_exp'],
            'top10_inclusion_freq': inc_prob,
            'median_resampled_rank': med_rank,
            'cutoff_status': verdict
        })
        
    df_cutoff = pd.DataFrame(cutoff_rows)
    df_cutoff.to_csv(OUT_DIR / 'phase10_cutoff_analysis.csv', index=False)
    print("Saved phase10_cutoff_analysis.csv")

    # =========================================================================
    # DELIVERABLE 8: RANK UNCERTAINTY MERGED
    # =========================================================================
    print("Generating Deliverable 8: Rank Uncertainty...")
    unc_rows = []
    
    for _, p in bat_candidates.iterrows():
        pid = p['player_id']
        p_rank = int(p['official_rank'])
        u = bat_unc.loc[pid] if pid in bat_unc.index else None
        unc_rows.append({
            'role': 'Batter',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p['player_name'],
            'cpri_score': p['cpri_score'],
            'top10_inclusion_freq': u['top10_inclusion_freq'] if u is not None else np.nan,
            'median_rank': u['median_rank'] if u is not None else np.nan,
            'rank_p5': u['rank_p5'] if u is not None else np.nan,
            'rank_p95': u['rank_p95'] if u is not None else np.nan,
            'rank_std': u['rank_std'] if u is not None else np.nan
        })
        
    for _, p in bowl_candidates.iterrows():
        pid = p['player_id']
        p_rank = int(p['official_rank'])
        u = bowl_unc.loc[pid] if pid in bowl_unc.index else None
        unc_rows.append({
            'role': 'Bowler',
            'official_rank': p_rank,
            'player_id': pid,
            'player_name': p['player_name'],
            'cpri_score': p['cpri_score'],
            'top10_inclusion_freq': u['top10_inclusion_freq'] if u is not None else np.nan,
            'median_rank': u['median_rank'] if u is not None else np.nan,
            'rank_p5': u['rank_p5'] if u is not None else np.nan,
            'rank_p95': u['rank_p95'] if u is not None else np.nan,
            'rank_std': u['rank_std'] if u is not None else np.nan
        })
        
    df_unc = pd.DataFrame(unc_rows)
    df_unc.to_csv(OUT_DIR / 'phase10_rank_uncertainty.csv', index=False)
    print("Saved phase10_rank_uncertainty.csv")
    
    print("\n" + "=" * 80)
    print("ALL 6 CSV DELIVERABLES GENERATED SUCCESSFULLY IN OUTPUT DIR!")
    print("=" * 80)

if __name__ == '__main__':
    main()
