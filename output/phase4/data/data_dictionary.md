# SupeRR Intelligence — Scouting Data Stores: Data Dictionary

**Version**: `1.0.0`  
**Parent Framework**: SupeRR Intelligence Phase 4.2 Scouting Store Builder  
**Methodology Freeze**: `CPRI-v1.0.0-PROD-FREEZE` (Phase 3.5)  
**Location**: `output/phase4/data/`  

---

## 1. Overview of Scouting Data Stores

Phase 4.2 constructs three compact, structured, queryable JSON data stores to power real-time AI scouting and analytics without reloading multi-gigabyte delivery files.

| File Name | Primary Purpose | Record Scope | Target Size |
|:---|:---|:---|:---:|
| [`player_scouting_profiles.json`](output/phase4/data/player_scouting_profiles.json) | Complete profile for each ranked player: CPRI scores, components, confidence tiers, exposure, baseline stats, and bootstrap uncertainty. | 60 Players (40 Official Top 10 + 20 Provisional Top 5) | ~0.2 MB |
| [`player_contextual_splits.json`](output/phase4/data/player_contextual_splits.json) | Situational breakdowns: Powerplay, Middle, Death, Pace vs Spin (Batters), vs RHB/LHB (Bowlers), and High vs Low Pressure contrasts. | 60 Players (40 Official Top 10 + 20 Provisional Top 5) | ~0.15 MB |
| [`head_to_head_matrix.json`](output/phase4/data/head_to_head_matrix.json) | Exhaustive batter vs bowler historical encounters in IPL and T20I with explicit sample size tiers and reliability indicators. | 25,985 Matchup Pairs (5,631 involving ranked players) | ~18 MB |

---

## 2. Store 1: `player_scouting_profiles.json`

### Field Definitions
- `profile_key` (string): Unique identifier formatted as `{competition_scope}_{role}_{player_id}`.
- `player_id` (integer): Official unique numeric player ID.
- `player_name` (string): Standardized player clean name.
- `competition_scope` (string): Tournament format: strictly `"IPL"` or `"T20I"`.
- `role` (string): Player specialization: strictly `"Batter"` or `"Bowler"`.
- `cohort` (string): Cohort designation: `"IPL Batters"`, `"T20I Batters"`, `"IPL Bowlers"`, or `"T20I Bowlers"`.
- `ranking_tier` (string): Official category: `"Official Top 10"` or `"Provisional Top 5"`.
- `official_rank` (integer): Rank within the designated cohort tier ($1$ to $10$ for Official, $1$ to $5$ for Provisional).
- `is_official_top10` (boolean): `true` if player achieved eligible Official Top 10 status.
- `is_provisional_top5` (boolean): `true` if player achieved Provisional Top 5 status (sub-threshold pressure sample).
- `is_champion` (boolean): `true` if player is the Rank 1 Official Champion in their cohort.
- `cpri_score` (float): Frozen Phase 3.5 composite CPRI score ($0.0$ to $100.0$).
- `components` (object):
  - `pressure_impact` (float): 40% weight.
  - `pressure_adaptability` (float): 25% weight.
  - `clutch_consistency` (float): 20% weight.
  - `reliability_confidence` (float): 15% weight.
- `confidence_tier` (string): `"High Confidence"` or `"Provisional"`.
- `status_reason` (string): Exact frozen rationale documenting qualification or provisional sample depth.
- `frozen_cpri_metrics` (object): Explicit container for authoritative Phase 3.5 frozen metrics:
  - `cpri_score`: Authoritative composite score.
  - `score_pressure_impact`, `score_adaptability`, `score_consistency`, `score_reliability`: Authoritative frozen component scores.
  - `frozen_pressure_deliveries`: 411 for Rinku Singh (match-state deliveries with pressure_score >= 50.0).
  - `frozen_total_deliveries`: Total delivery events.
  - `frozen_pressure_matches`: Matches with pressure.
- `exposure` (object):
  - `total_deliveries`: Total match-state deliveries in scope.
  - `pressure_deliveries`: Total deliveries under pressure ($\text{Pressure Score} \ge 50.0$). Authoritative Phase 3.5 count.
  - `pressure_matches`: Unique matches with pressure.
  - `sample_definition_notes`: Documentation distinguishing match-state pressure deliveries from striker balls faced.
  - `total_matches`: Total matches played.
  - `balls_per_match`: Average legal balls per match (specialist workload metric for bowlers).
  - `pressure_ratio`: $\text{pressure\_deliveries} / \text{total\_deliveries}$.
  - `pos_pressure_match_ratio`: Fraction of pressure matches with positive net performance residual.
  - `effective_pressure_sample_size`: Harmonic/cluster-discounted effective sample size ($n_{eff}$).
  - `pressure_specific_uncertainty`: Uncertainty score ($0.0$ to $100.0$).
- `performance_stats` (object):
  - **For Batters**: `balls_faced`, `actual_runs`, `strike_rate`, `batting_average`, `dismissals`, `fours`, `sixes`, `boundary_runs`, `boundary_percentage`, `dot_balls`, `dot_percentage`, and nested `pressure_stats` / `nonpressure_stats` (runs, balls, SR, average, WPA, run residual).
  - **For Bowlers**: `balls_bowled`, `overs_bowled`, `runs_conceded`, `credited_wickets`, `economy_rate`, `bowling_average`, `bowling_strike_rate`, `fours_conceded`, `sixes_conceded`, `boundary_percentage`, `dot_balls`, `dot_percentage`, and nested `pressure_stats` / `nonpressure_stats` (runs conceded, overs, wickets, economy, bowling average, WPA, run residual).
- `bootstrap_uncertainty` (object):
  - `is_audited` (boolean): `true` for Official Top 10 players audited under Phase 3.5 bootstrap simulation.
  - `primary_resampling_standard`: Resampling unit (Match-Level for IPL, Series-Level for T20I).
  - `prob_eligibility_pct`: Probability of meeting sample size thresholds across resampled replicates.
  - `prob_rank_1_pct`: Frequency of achieving Rank 1.
  - `prob_top10_pct`: Frequency of inclusion in Top 10.
  - `conditional_rank_median`: Median rank across eligible bootstrap replicates.
  - `conditional_rank_95_interval`: 95% empirical bootstrap rank interval `"[lower, upper]"`.
  - `conditional_cpri_mean`: Mean CPRI score across eligible bootstrap replicates.
  - `conditional_cpri_std_dev`: Statistical standard deviation of CPRI across replicates.
  - `conditional_cpri_95_ci`: 95% empirical bootstrap CPRI confidence interval.
  - `mc_standard_error_rank1_pct`: Monte Carlo standard error for Rank 1 probability ($SE_{MC} = \sqrt{p(1-p)/B}$).
  - `mc_standard_error_top10_pct`: Monte Carlo standard error for Top 10 probability.

---

## 3. Store 2: `player_contextual_splits.json`

### Field Definitions
- `innings_phase_splits` (object):
  - `powerplay`: Overs 1 to 6 (Deliveries with field restriction rules active).
  - `middle`: Overs 7 to 16 (Middle innings strike rotation and spin handling).
  - `death`: Overs 17 to 20 (High-leverage terminal overs).
- `bowling_type_splits` (Batters only):
  - `pace`: Performance against Pace / Seam bowlers.
  - `spin`: Performance against Spin bowlers (Off-spin, Leg-spin, SLA).
- `batter_hand_splits` (Bowlers only):
  - `rhb`: Performance against Right-Hand Batters.
  - `lhb`: Performance against Left-Hand Batters.
- `pressure_contrast` (object):
  - `high_pressure`: Deliveries where $\text{Pressure Score} \ge 50.0$.
  - `low_pressure`: Deliveries where $\text{Pressure Score} < 50.0$.
  - `delta_strike_rate` (Batters): $SR_{high} - SR_{low}$. Positive indicates acceleration under pressure.
  - `delta_economy` (Bowlers): $Econ_{high} - Econ_{low}$. Negative indicates improved run restriction under pressure.
  - `tactical_classification`:
    - Batters: `"Clutch Accelerant"` ($\Delta SR \ge +5.0$), `"Pressure Degrader"` ($\Delta SR \le -5.0$), or `"Anchor Stabilizer"` ($|\Delta SR| < 5.0$).
    - Bowlers: `"High-Leverage Constrictor"` ($\Delta Econ \le -0.50$), `"Pressure Vulnerable"` ($\Delta Econ \ge +0.50$), or `"Steady Executor"` ($|\Delta Econ| < 0.50$).

---

## 4. Store 3: `head_to_head_matrix.json`

### Sample Limitation Tiers
Every head-to-head record includes an explicit `sample_tier` to prevent LLMs from hallucinating certainty on low-sample encounters:
1. **`Very Low Sample (<6 balls)`**: Exploratory sample ($< 6$ balls). Variance completely dominates statistical signal. Tactical conclusions prohibited.
2. **`Low Sample (6-17 balls)`**: Early sample ($6\text{--}17$ balls). Indicates early tendencies; wide uncertainty intervals.
3. **`Moderate Sample (18-29 balls)`**: Indicative sample ($18\text{--}29$ balls). Emerging tactical trend with meaningful historical weight.
4. **`Robust Sample (>=30 balls)`**: Statistically reliable sample ($\ge 30$ balls). High statistical confidence for tactical planning.

### Metrics Computed
- `balls_faced`: Legal balls faced by the batter from this specific bowler.
- `runs_scored`: Total runs scored off the bat against this bowler.
- `dismissals`: Credited dismissals where bowler took batter's wicket (`bowler_wicket == 1`).
- `fours` & `sixes`: Boundaries hit by batter off bowler.
- `dot_balls`: Deliveries with zero runs scored off the bat.
- `strike_rate`: $(Runs / Balls) \times 100$.
- `batting_average`: $Runs / Dismissals$ (or `null` if $0$ dismissals).
- `balls_per_dismissal`: $Balls / Dismissals$ (or `null` if $0$ dismissals).
- `dot_percentage`: $(DotBalls / Balls) \times 100$.
- `boundary_percentage`: $((Fours + Sixes) / Balls) \times 100$.
- `avg_pressure_score`: Average game pressure score during this matchup.
- `is_statistically_reliable`: `true` if $\text{balls\_faced} \ge 18$.
- `ranked_player_involved`: `true` if batter or bowler belongs to the 60 official/provisional ranked players.
