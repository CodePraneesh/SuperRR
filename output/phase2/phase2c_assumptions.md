# SupeRR Intelligence — Phase 2C Assumptions & Methodological Documentation

## 1. Scope & Competition Baselines
- **Included Competitions**: Indian Premier League (IPL) and Twenty20 International (T20I).
- **Excluded Competitions**: Emerging Teams T20 matches (30 matches) are strictly filtered out from all model training, calibration, and player baseline rankings (in_scope_competition == False).
- **Abandoned / Incomplete Matches**: 41 matches marked as abandoned, no result, or untied with missing winner (e.g. match ID 18532) are excluded from outcome-based win probability model training.
- **Independence of Competitions**: IPL and T20I dynamics differ in scoring rates and par totals. Features include format identifiers (is_ipl) and historical venue/format par scores (IPL: 186 runs; T20I: 171 runs).

---

## 2. Temporal Partitioning (Zero-Lookahead Guarantee)
All win probability models are trained strictly on chronological historical data:
- **Chronological Split**: 812 total valid matches sorted by match_date.
  - **Train Set**: 568 matches (70.0%) spanning 2022-01-22 to 2025-05-26 (135,085 deliveries).
  - **Validation Set**: 122 matches (15.0%) spanning 2025-05-27 to 2026-01-31.
  - **Test Set (Out-of-Sample)**: 122 matches (15.0%) spanning 2026-02-01 to 2026-11-01 (28,639 deliveries).
- **Strict Pre-Delivery Features**: Win probability before delivery P(win before) uses only features known before the delivery is bowled. No concurrent runs, wickets, or subsequent innings data are leaked.

---

## 3. Pre-Delivery Feature Sets

### 3.1 Chasing Model (Innings 2)
The chasing model estimates the probability that the chasing team successfully reaches the target:
- runs_req_clean: Runs needed to achieve victory (max(0, target - score_before)).
- balls_remaining: Balls remaining in the 20-over allotment (max(0, 120 - legal_balls_before)).
- wickets_in_hand: Wickets remaining (max(0, 10 - wickets_lost_before)).
- wickets_lost_before: Number of wickets fallen.
- rrr_clean: Required Run Rate per 6 balls.
- crr_clean: Current Run Rate achieved.
- score_before: Runs scored up to this point.
- target_clean: First innings target score.
- is_ipl: Binary competition indicator (IPL vs. T20I).
- innings_phase: Binary indicators for Powerplay (overs 0-5), Middle (overs 6-14), and Death (overs 15-19).
- pressure_score: Pre-delivery Dynamic Pressure Score [0, 100] developed in Phase 2A.

### 3.2 First-Innings Model (Innings 1)
Estimates the probability that the first-innings batting team will defend their score:
- score_before, wickets_lost_before, balls_remaining, wickets_in_hand, crr_clean.
- format_par_score: Contextual benchmark (186.0 for IPL, 171.0 for T20I).
- expected_final_total: Projected par score given balls remaining and current scoring tempo.
- is_ipl, pressure_score, innings_phase.

---

## 4. State Transitions & Terminal State Resolution
Delivery Win Probability Added (WPA) is calculated as:
WPA_delivery = P(win after delivery) - P(win before delivery)

### 4.1 Transition Rules
- score_after = score_before + total_delivery_runs
- wickets_lost_after = wickets_lost_before + is_team_wicket
- legal_balls_after = legal_balls_before + legal_ball
- balls_remaining_after = max(0, 120 - legal_balls_after)
- wickets_in_hand_after = max(0, 10 - wickets_lost_after)

### 4.2 Terminal Match States (Innings 2)
1. **Target Reached**: If runs_req_after <= 0, P(win after) = 1.0.
2. **All Out**: If wickets_in_hand_after == 0 and runs_req_after > 0, P(win after) = 0.0.
3. **Balls Exhausted without Target**: If balls_remaining_after == 0 and runs_req_after > 1.0, P(win after) = 0.0.
4. **Tie on Final Ball**: If balls_remaining_after == 0 and runs_req_after == 1.0, P(win after) = 0.50 (Super Over).
5. **Wicket Monotonicity Constraint**: In chasing innings, losing a wicket without simultaneously reaching the target cannot increase batting team win probability ceteris paribus (P(win after) <= P(win before)).

---

## 5. Player Attribution Principles & Sign Conventions
Total delivery WPA is apportioned into three distinct components:
WPA_delivery = WPA_batting + WPA_bowling_team + WPA_unattributed

### 5.1 Sign Conventions
- **Batting WPA**: Positive values indicate the striker increased the batting team win probability.
- **Bowling WPA**: Strictly from the **bowling team perspective**. Positive values indicate the bowler performed well and increased the bowling team win probability:
  WPA_bowler = -(WPA_delivery_assigned_to_bowler)
  - Taking a wicket or conceding a dot ball yields **positive** bowling WPA.
  - Conceding a boundary or bowling a wide yields **negative** bowling WPA.

### 5.2 Attribution Rules by Delivery Event
1. **Byes and Leg-Byes**:
   - Extras conceded through byes or leg-byes are fielding/wicket-keeping events, not bowler or striker errors.
   - Attributed 100% to WPA_unattributed. Striker and Bowler receive 0.0.
2. **Wides**:
   - Pure bowling execution error.
   - If stumping occurs on a wide, bowler is credited with taking a wicket: WPA_bowler = -WPA_delivery > 0.
   - Otherwise, charged to bowler: WPA_bowler = -WPA_delivery < 0. Striker receives 0.0.
3. **No-Balls (Overstep)**:
   - Bowler conceded penalty extra. If batter scores off the no-ball, the win probability gain is split proportionally based on batter runs vs total runs.
4. **Ambiguous Extras ('other', 'penalty', unlabelled)**:
   - Allocated 100% to WPA_unattributed to ensure unverified data does not distort player rankings.
5. **Legitimate Bowler Wickets (Bowled, Caught, LBW, Stumped, Hit Wicket)**:
   - Dismissal leverage is shared 50/50:
     - Striker penalty: WPA_batting = WPA_delivery * 0.50 <= 0.
     - Bowler credit: WPA_bowler = -WPA_delivery * 0.50 >= 0.
6. **Non-Bowler Dismissals (Run Out, Retired Out, Obstructing Field)**:
   - Charged as team/fielding events to WPA_unattributed. Bowler does not receive unearned wicket credit.
7. **Normal Scoring Deliveries**:
   - Shared 50/50 between striker shot execution and bowler defensive containment:
     - WPA_batting = WPA_delivery * 0.50
     - WPA_bowler = -WPA_delivery * 0.50

---

## 6. Sample-Size Confidence Tiers
To avoid hiding low-sample players while preserving statistical integrity, all players are tagged with transparent confidence tiers:
- **High Confidence**: >= 150 deliveries.
- **Moderate Confidence**: 60 - 149 deliveries.
- **Low Confidence**: < 60 deliveries.
Small-sample players are fully inspectable with documented sample size and per-100-ball rates.
