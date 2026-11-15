#!/usr/bin/env python3
'''
wpa_attribution.py
Phase 2C: WPA Player Attribution Rules & Summary Aggregator.
Explicitly divides delivery WPA into:
- Batting WPA (credited to striker)
- Bowling WPA (credited to bowler, positive = good bowling)
- Unattributed / Team Event WPA (byes, legbyes, run-outs, ambiguous extras)
'''
from __future__ import annotations
import numpy as np
import pandas as pd

def attribute_delivery_wpa(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Applies principled cricket attribution to delivery WPA:
    Total Delivery WPA = Batting WPA + Bowling Team WPA + Team/Extra WPA.
    
    Sign Conventions:
    - batting_wpa: Positive = helped batting team (credited to striker).
    - bowling_wpa: Positive = helped bowling team (credited to bowler).
      Note: bowling_wpa = -(delivery_wpa_assigned_to_bowler).
    - team_unattributed_wpa: Byes, leg-byes, run-outs, ambiguous extras.
    '''
    d = df.copy()
    dwpa = d['delivery_wpa'].values
    
    b_runs = d['batter_runs'].values
    tot_runs = d['total_delivery_runs'].values
    is_wkt = d['is_wicket'].values
    bowler_wkt = d['bowler_wicket'].values
    ex_label = d['extras_label'].values
    
    is_unknown_extra = d['is_unknown_extra'].values
    
    bat_wpa = np.zeros(len(d), dtype=float)
    bowl_wpa = np.zeros(len(d), dtype=float)
    unattr_wpa = np.zeros(len(d), dtype=float)
    
    for i in range(len(d)):
        w = dwpa[i]
        extra = ex_label[i]
        
        # 1. Byes / Leg-byes (Batting Team Extras, not batter or bowler)
        if extra in ['byes', 'legbyes']:
            # The runs are byes/leg-byes; if a run-out occurs, it is fielding
            unattr_wpa[i] = w
            
        # 2. Wides / No-balls
        elif extra in ['wide', 'overstep']:
            if extra == 'wide':
                # Wides are bowler errors (-WPA for bowler, positive for bowling_wpa if -w > 0)
                # If stumping on wide, bowler gets credit!
                if bowler_wkt[i]:
                    bowl_wpa[i] = -w # bowler took wicket on wide
                else:
                    bowl_wpa[i] = -w # wide penalty charged to bowler
            else: # overstep no-ball
                # Batter can hit runs on no-ball
                if b_runs[i] > 0:
                    run_frac = b_runs[i] / max(1, tot_runs[i])
                    bat_wpa[i] = w * run_frac
                    bowl_wpa[i] = -(w * (1.0 - run_frac)) # bowler conceded penalty
                else:
                    bowl_wpa[i] = -w
                    
        # 3. Ambiguous Extras ('other', 'Penalty', unlabelled)
        elif is_unknown_extra[i]:
            # Mark completely as unattributed to prevent corrupting player rankings
            unattr_wpa[i] = w
            
        # 4. Standard Deliveries
        else:
            if is_wkt[i]:
                if bowler_wkt[i]:
                    # Legitimate Bowler Wicket (Bowled, Caught, LBW, Stumped, Hit Wicket)
                    # Wicket lowers batting win prob (w < 0).
                    # Bowler gets credit: bowling_wpa = -w > 0
                    # Batter gets penalty: bat_wpa = w < 0
                    # Equal distribution of dismissal leverage:
                    bat_wpa[i] = w * 0.50
                    bowl_wpa[i] = -w * 0.50
                else:
                    # Non-bowler dismissal: Run Out, Retired Out, Obstructing Field
                    # Run out / tactical dismissal is an unattributed / fielding event
                    unattr_wpa[i] = w
            else:
                # Normal run-scoring delivery
                # Positive runs increase batting win prob (w > 0)
                # Batter gets positive credit; bowler gets negative credit (bowling_wpa = -w)
                # Split leverage 50/50 between batter execution and bowler defense
                bat_wpa[i] = w * 0.50
                bowl_wpa[i] = -w * 0.50
                
    d['batting_wpa'] = bat_wpa
    d['bowling_wpa'] = bowl_wpa
    d['unattributed_wpa'] = unattr_wpa
    
    return d

def aggregate_player_wpa(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Aggregates delivery WPA into comprehensive player-level summaries for IPL and T20I.
    '''
    d = df.copy()
    d['is_pressure'] = d['pressure_score'].ge(50.0)
    
    # Batter Aggregation
    bat_records = []
    for (pid, pname, scope), grp in d.groupby(['striker_id', 'striker_name_clean', 'competition_scope']):
        total_balls = len(grp)
        tot_bat_wpa = grp['batting_wpa'].sum()
        
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        p_bat_wpa = p_grp['batting_wpa'].sum() if p_balls > 0 else 0.0
        
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        np_bat_wpa = np_grp['batting_wpa'].sum() if np_balls > 0 else 0.0
        
        matches = grp['match_id'].nunique()
        tier = 'High Confidence' if total_balls >= 150 else ('Moderate Confidence' if total_balls >= 60 else 'Low Confidence')
        
        bat_records.append({
            'player_id': pid, 'player_name': pname, 'competition_scope': scope,
            'role': 'Batter', 'matches': matches, 'total_deliveries': total_balls,
            'pressure_deliveries': p_balls, 'total_wpa': round(tot_bat_wpa, 4),
            'wpa_per_100_balls': round(100.0 * (tot_bat_wpa / total_balls), 4),
            'pressure_wpa': round(p_bat_wpa, 4), 'nonpressure_wpa': round(np_bat_wpa, 4),
            'confidence_tier': tier
        })
        
    # Bowler Aggregation
    bowl_records = []
    for (pid, pname, scope), grp in d.groupby(['bowler_id', 'bowler_name_clean', 'competition_scope']):
        total_balls = len(grp)
        tot_bowl_wpa = grp['bowling_wpa'].sum()
        
        p_grp = grp[grp['is_pressure']]
        p_balls = len(p_grp)
        p_bowl_wpa = p_grp['bowling_wpa'].sum() if p_balls > 0 else 0.0
        
        np_grp = grp[~grp['is_pressure']]
        np_balls = len(np_grp)
        np_bowl_wpa = np_grp['bowling_wpa'].sum() if np_balls > 0 else 0.0
        
        matches = grp['match_id'].nunique()
        tier = 'High Confidence' if total_balls >= 150 else ('Moderate Confidence' if total_balls >= 60 else 'Low Confidence')
        
        bowl_records.append({
            'player_id': pid, 'player_name': pname, 'competition_scope': scope,
            'role': 'Bowler', 'matches': matches, 'total_deliveries': total_balls,
            'pressure_deliveries': p_balls, 'total_wpa': round(tot_bowl_wpa, 4),
            'wpa_per_100_balls': round(100.0 * (tot_bowl_wpa / total_balls), 4),
            'pressure_wpa': round(p_bowl_wpa, 4), 'nonpressure_wpa': round(np_bowl_wpa, 4),
            'confidence_tier': tier
        })
        
    summary_df = pd.concat([pd.DataFrame(bat_records), pd.DataFrame(bowl_records)], ignore_index=True)
    return summary_df.sort_values(['competition_scope', 'role', 'total_wpa'], ascending=[True, True, False]).reset_index(drop=True)
