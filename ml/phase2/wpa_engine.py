#!/usr/bin/env python3
'''
wpa_engine.py
Phase 2C: Win Probability Added (WPA) Engine.
Computes post-delivery state transition and delivery-level WPA:
WPA = P(win after delivery) - P(win before delivery).
Guarantees consistent batting-team perspective and correct terminal states.
'''
from __future__ import annotations
import numpy as np
import pandas as pd
from ml.phase2.win_probability import (
    prepare_win_prob_features,
    ChasingWinProbabilityModel,
    FirstInningsWinProbabilityModel
)

def compute_post_delivery_state(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Constructs the immediate post-delivery state using the observed delivery outcome
    and verified Phase 1 cricket transition rules. Strictly zero future-ball leakage.
    '''
    post = df.copy()
    
    # 1. State transition
    # Score after delivery
    post['score_after'] = post['score_before'] + post['total_delivery_runs']
    # Wickets lost after delivery
    post['wickets_lost_after'] = post['wickets_lost_before'] + post['is_team_wicket'].astype(int)
    # Legal balls bowled after delivery
    post['legal_balls_after'] = post['legal_balls_before'] + post['legal_ball'].astype(int)
    
    # Update post-delivery remaining resources
    total_balls = post['overs_limit'] * 6.0
    post['balls_remaining_after'] = np.maximum(0, total_balls - post['legal_balls_after'])
    post['wickets_in_hand_after'] = np.maximum(0, 10 - post['wickets_lost_after'])
    
    # Current run rate after delivery
    post['crr_clean_after'] = np.where(
        post['legal_balls_after'] > 0,
        post['score_after'] / (post['legal_balls_after'] / 6.0),
        8.0
    ).clip(0.0, 36.0)
    
    # Chasing metrics after delivery
    post['runs_req_after'] = np.where(
        post['innings'] == 2,
        np.maximum(0.0, post['target_clean'] - post['score_after']),
        0.0
    )
    post['rrr_clean_after'] = np.where(
        (post['innings'] == 2) & (post['balls_remaining_after'] > 0),
        post['runs_req_after'] / (post['balls_remaining_after'] / 6.0),
        np.where(post['runs_req_after'] <= 0.0, 0.0, 36.0)
    ).clip(0.0, 36.0)
    
    # Phase after delivery
    overs_elapsed_after = post['legal_balls_after'] / 6.0
    death_start = np.maximum(0, post['overs_limit'] - 5)
    post['is_powerplay_after'] = (overs_elapsed_after < np.minimum(6, post['overs_limit'])).astype(int)
    post['is_death_after'] = (overs_elapsed_after >= death_start).astype(int)
    post['is_middle_after'] = (1 - post['is_powerplay_after'] - post['is_death_after']).clip(0, 1)
    
    return post

class WPAEngine:
    '''
    Engine computing P(win before) and P(win after) to calculate delivery WPA.
    '''
    def __init__(self):
        self.chase_model = ChasingWinProbabilityModel()
        self.inn1_model = FirstInningsWinProbabilityModel()

    def fit(self, train_df: pd.DataFrame):
        d_prep = prepare_win_prob_features(train_df)
        train_chase = d_prep[d_prep['innings'] == 2]
        train_inn1 = d_prep[d_prep['innings'] == 1]
        
        print(f'Fitting chasing model on {len(train_chase)} deliveries...')
        self.chase_model.fit(train_chase)
        
        print(f'Fitting 1st innings model on {len(train_inn1)} deliveries...')
        self.inn1_model.fit(train_inn1)

    def calculate_delivery_wpa(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Calculates pre-delivery win prob, post-delivery win prob, and delivery WPA.
        '''
        d = prepare_win_prob_features(df)
        post = compute_post_delivery_state(d)
        
        # 1. Pre-delivery Win Probability (batting team perspective)
        pre_probs = np.zeros(len(d), dtype=float)
        
        # Innings 2 Pre-probs
        mask_inn2 = (d['innings'] == 2).values
        if mask_inn2.any():
            pre_probs[mask_inn2] = self.chase_model.predict_proba(d[mask_inn2])
            
        # Innings 1 Pre-probs
        mask_inn1 = (d['innings'] == 1).values
        if mask_inn1.any():
            pre_probs[mask_inn1] = self.inn1_model.predict_proba(d[mask_inn1])
            
        # Innings 3+ (Super Over) default
        mask_so = (d['innings'] >= 3).values
        if mask_so.any():
            pre_probs[mask_so] = 0.50
            
        d['p_win_before'] = pre_probs
        
        # 2. Post-delivery Win Probability (batting team perspective)
        # Create input dataframe for post-delivery prediction
        post_input = d.copy()
        post_input['score_before'] = post['score_after']
        post_input['wickets_lost_before'] = post['wickets_lost_after']
        post_input['balls_remaining'] = post['balls_remaining_after']
        post_input['wickets_in_hand'] = post['wickets_in_hand_after']
        post_input['crr_clean'] = post['crr_clean_after']
        post_input['runs_req_clean'] = post['runs_req_after']
        post_input['rrr_clean'] = post['rrr_clean_after']
        post_input['is_powerplay'] = post['is_powerplay_after']
        post_input['is_middle'] = post['is_middle_after']
        post_input['is_death'] = post['is_death_after']
        
        post_probs = np.zeros(len(d), dtype=float)
        
        # Innings 2 Post-probs (Terminal States strictly resolved)
        if mask_inn2.any():
            # Check terminal states explicitly
            chase_post = post_input[mask_inn2]
            runs_req = post.loc[mask_inn2, 'runs_req_after'].values
            wkts_left = post.loc[mask_inn2, 'wickets_in_hand_after'].values
            balls_rem = post.loc[mask_inn2, 'balls_remaining_after'].values
            
            raw_post_probs = self.chase_model.predict_proba(chase_post)
            # Terminal overrides:
            # Reached target: win = 1.0
            # All out without target: loss = 0.0
            # Balls exhausted: runs_req == 1 is tie (0.5), runs_req > 1 is loss (0.0)
            term_post = np.where(runs_req <= 0.0, 1.0,
                        np.where(wkts_left <= 0, 0.0,
                        np.where((balls_rem <= 0) & (runs_req > 1.0), 0.0,
                        np.where((balls_rem <= 0) & (runs_req == 1.0), 0.5, raw_post_probs))))
            
            # Monotonicity constraint on wicket deliveries:
            # Losing a wicket (team wicket) cannot increase batting team win probability
            # unless the target has already been achieved (runs_req <= 0.0).
            is_wkt_inn2 = post.loc[mask_inn2, 'is_team_wicket'].values
            pre_p_inn2 = pre_probs[mask_inn2]
            term_post = np.where(is_wkt_inn2 & (runs_req > 0.0), np.minimum(term_post, pre_p_inn2), term_post)
            post_probs[mask_inn2] = term_post
            
        # Innings 1 Post-probs
        if mask_inn1.any():
            inn1_post = post_input[mask_inn1]
            raw_inn1_post = self.inn1_model.predict_proba(inn1_post)
            # If all out in inn 1, probability is pegged to completed score
            post_probs[mask_inn1] = raw_inn1_post
            
        if mask_so.any():
            post_probs[mask_so] = 0.50
            
        d['p_win_after'] = post_probs
        
        # 3. Delivery WPA (Batting Team Perspective)
        # Positive = increases batting team win probability
        # Negative = decreases batting team win probability
        d['delivery_wpa'] = d['p_win_after'] - d['p_win_before']
        
        return d
