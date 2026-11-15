# Phase 1 Assumptions Register

This document records all explicit, testable, and transparent domain assumptions adopted for the SupeRR Intelligence Phase 1 cricket data pipeline. In accordance with senior cricket data engineering standards, no ambiguous rules have been silently invented.

---

## 1. Competition Scope & Tier Separation
- **Official Scope**: Defined strictly as Indian Premier League (IPL) and Twenty20 International (T20I) fixtures.
- **Emerging Teams T20 Exclusion**: The archive contains 30 matches from 'Mens T20 Emerging Teams Asia Cup 2024' (15 matches) and 'Asia Cup Rising Stars 2025' (15 matches). These matches are retained in full in the delivery-level audit dataset with \in_scope_competition = False\ and \competition_scope = 'Emerging_T20'\, but are strictly excluded from official player baseline computations.
- **Scope Segmentation**: Player baseline aggregates (\atter_baselines_provisional.csv\ and \owler_baselines_provisional.csv\) explicitly separate player metrics by \competition_scope\ ('IPL' vs 'T20I').

---

## 2. Wicket Attribution & Bowler Crediting
- **Credited Dismissals**: Only dismissals where the bowler actively caused the dismissal under MCC Law 21/33/35/36/39 are credited:
  - **Bowled**
  - **Caught**
  - **LBW**
  - **Stumped** (\Stump\)
  - **Hit Wicket**
- **Excluded Dismissals**:
  - **Run Out** (\RunOut\) — attributed as a team wicket, never credited to the bowler.
  - **Retired Out** (\Retire Out\) — tactical batting dismissal, never credited to the bowler.
  - **Obstructing the Field** (\Obstructing the field\ / \Obstracting the field\) — batsman breach, never credited to the bowler.
- **Delivery Exceptions**:
  - **No-ball Deliveries** (\Overstep\): By MCC Law, a bowler cannot take a wicket on a no-ball (except run out or obstruction). Any dismissal on a no-ball is strictly excluded from bowler wicket credit.
  - **Ambiguous-Extra Deliveries** (\other\, \Penalty\, or unlabelled non-zero extras): Because delivery legality cannot be validated without primary scoring documentation, wickets on ambiguous deliveries are excluded from bowler credit.
- **Team Wickets**: All dismissed instances (\is_wicket == True\) are retained in \is_team_wicket\ for cumulative innings wickets lost and innings progression.

---

## 3. Deliveries and Extras Handling
- **Batter Runs**: Sourced from \all_by_ball.runs\. Boundary flags (\is_four\ and \is_six\) disagree on 23 deliveries (e.g. 1 run scored with \is_four == True\ / \is_six == True\). The pipeline preserves raw runs and derives verified boundaries via \uns == 4\ and \uns == 6\.
- **Extras Components**: Retained cleanly as \extras1\ (\extras1_runs\) and \extras2\ (\extras_2_runs\). Delivery total runs are calculated as \atter_runs + extras1 + extras2\.
- **Wides**:
  - Wides (\extras_type == 'wide'\) are illegal balls (\legal_ball = False\).
  - Do not count as balls faced by the batter (\atter_faced_ball = False\).
  - Charged to bowler runs conceded (\extras1 + extras2\).
- **No-Balls (Overstep)**:
  - No-balls are illegal balls (\legal_ball = False\).
  - Count as balls faced by the batter (\atter_faced_ball = True\).
  - 1 run penalty charged to bowler conceded runs (\extras1\).
- **Byes & Leg-Byes**:
  - Count as legal deliveries (\legal_ball = True\).
  - Count as balls faced by the batter (\atter_faced_ball = True\).
  - Never charged to the bowler (\owler_runs_conceded = batter_runs\).
- **Ambiguous Extras ('other', 'Penalty', unlabelled)**:
  - Treated with caution (\legal_ball = False\, \owler_runs_conceded_known = False\).
  - Retained for inspection rather than silently discarded or forced into standard buckets.

---

## 4. Match-State & Lookahead Prevention
- **Point-in-Time Integrity**: All sequential match-state features (\score_before\, \wickets_lost_before\, \legal_balls_before\) are derived via cumulative sums strictly shifted by 1 delivery (\cumsum().shift(fill_value=0)\).
- **Zero Lookahead Guarantee**: On ball 1 of every innings, state is strictly zero. All pressure metrics and required/current run rates use strictly prior-to-delivery information.
- **Chasing Target**: Second innings target is \irst_innings_total + 1\, unless an official \evised_target\ (DLS/VJD) is provided in match metadata.

---

## 5. Super Overs & Extra Innings
- **Super Overs**: Innings 3 and 4 represent Super Overs (38 deliveries across 6 matches).
- **Baseline Exclusion**: All deliveries with \innings >= 3\ are fully preserved in \deliveries_enriched.csv\ for ball-by-ball analysis, but are strictly excluded from standard T20/T20I career and seasonal baseline aggregates (\atter_baselines_provisional.csv\ and \owler_baselines_provisional.csv\).

---

## 6. Playing XI & Player Mappings
- **Duplicates**: 40 records in \playing_eleven\ feature identical \match_id\, \	eam_id\, and \player_id\ (frequently associated with impact substitutes or batting order revisions). These are diagnosed in \playing_eleven_deduplicated_diagnostic.csv\ using the earliest batting order, while preserving raw source tables.
- **Unmapped Strikers**: 83 striker deliveries did not match the static Playing XI table (attributable to late substitutions / impact player rules). Fallback to source delivery player names ensures zero data loss.
- **Matches Without Ball Data**: 16 matches in match metadata have zero ball-by-ball records. Audit reveals all 16 matches were officially 'Match Abandoned' without a ball bowled.
