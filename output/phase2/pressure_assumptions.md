# Phase 2A: Dynamic Pressure Engine — Assumptions & Domain Principles

This document records the mathematical specifications, cricket analytics rationales, and domain assumptions implemented in the Phase 2A Dynamic Pressure Detection Engine for **SupeRR Intelligence**.

---

## 1. Core Engineering & Anti-Leakage Principles

1. **Strict Pre-Delivery State (Zero Lookahead)**:
   - A player facing or bowling a delivery cannot know the outcome of that delivery beforehand.
   - All input features—including score, wickets lost, legal balls bowled, balls remaining, current run rate, required run rate, and wickets in hand—are derived strictly from events occurring prior to the current ball (\shift(fill_value=0)\).
   - Ball 1 of every innings strictly starts with \score_before = 0\, \wickets_lost_before = 0\, and \legal_balls_before = 0\.

2. **Contextual Difficulty vs Player Performance**:
   - The pressure score (0–100) measures **contextual demand / match leverage**, NOT how well or poorly the player performs on that delivery.
   - A delivery requiring 18 runs off 6 balls with 2 wickets in hand is categorized as 95+ pressure regardless of whether the batter hits a six, edges a four, or gets bowled.

3. **Innings Segregation & Distinguishability**:
   - First-innings pressure and second-innings (chasing) pressure represent distinct decision-theoretic environments and are evaluated through separate mathematical models.
   - In \pressure_scored_deliveries.csv\, \irst_innings_pressure_score\ and \chasing_pressure_score\ are explicitly maintained in separate columns alongside the master \pressure_score\.

4. **Competition Scope & Emerging Teams Exclusion**:
   - Official scope is strictly limited to **IPL** and **T20I** matches.
   - 30 Emerging Teams T20 matches (6,985 balls) are retained with \competition_scope = 'Emerging_T20'\ and \in_scope_competition = False\ for audit completeness, but are strictly excluded from official baseline distributions and rankings.

5. **Exclusion of Incomplete & Abandoned Matches from Training**:
   - 40 matches in match metadata were abandoned without a ball bowled or interrupted prematurely without official results.
   - These match IDs are strictly excluded from the training target of the historical expected-remaining-runs model to avoid training on truncated totals.

---

## 2. First-Innings Pressure Architecture

In the first innings, teams do not chase a fixed target; instead, they operate in an **economic maximization regime** against a league/venue par score under resource constraints (120 legal balls and 10 wickets).

### Expected Remaining Runs Model
- **Target**: Eventual innings total minus \score_before\.
- **Model Architecture**: \HistGradientBoostingRegressor\ trained strictly on pre-delivery features (\alls_remaining\, \wickets_in_hand\, \score_before\, \crr_clean\, \is_powerplay\, \is_death\).
- **Validation**: Evaluated using chronological train/test splits (75% past matches, 25% future matches). Achieved an Out-of-Sample \(R^2\) of **0.8014** and MAE of **18.38 runs** (dramatically outperforming naive Duckworth-Lewis linear resource models with MAE > 35.9).

### First-Innings Pressure Components
1. **Par Deficit Factor (35% Weight)**:
   - Evaluates the difference between the format benchmark par score (\(186.0\) in IPL, \(171.0\) in T20I) and the model's projected final innings total (\(\text{score\_before} + \text{expected\_remaining\_runs}\)).
   - Teams projected below par experience elevated urgency.
2. **Wicket Scarcity Factor (35% Weight)**:
   - Modelled as a super-linear scarcity curve: \((1.0 - \text{wickets\_in\_hand}/10.0)^{1.5}\).
   - Early wickets (top 3) introduce strategic caution; late wickets (tail exposed) dramatically spike batting pressure.
3. **Phase & Time Urgency (20% Weight)**:
   - Scales with overs elapsed and accelerates in the death overs (\(\text{is\_death} = 1\)), where dot balls carry severe penalty.
4. **Scoring Drag Penalty (10% Weight)**:
   - Penalizes sluggish run-rate performance relative to contemporary T20 standards.

---

## 3. Second-Innings (Chasing) Pressure Architecture

In the second innings, pressure is governed by a **deterministic target chase** where balls remaining and wickets remaining dictate instantaneous win probability.

### Chasing Pressure Components
1. **Required Run Rate Escalation (45% Weight)**:
   - S-curve progression: RRR of 6.0 RPO is low pressure (\(\approx 12\)); 9.0–10.0 RPO is moderate-to-high (\(\approx 45–60\)); >15.0 RPO enters severe crisis (\(\ge 90\)).
   - Evaluated as \(\tanh((\text{RRR} / 14.0)^{1.3})\).
2. **Resource Scarcity / Ball Depletion (30% Weight)**:
   - Evaluates the ratio of balls remaining to runs required (\(\text{balls\_per\_run}\)).
   - When \(\text{balls\_per\_run} < 1.0\), batting teams operate in a structural deficit.
3. **Wicket Depletion vs Runs Needed (25% Weight)**:
   - Measured as \(\text{runs\_required} / \text{wickets\_in\_hand}\).
   - If 60 runs are needed with 2 wickets in hand (\(30\) runs/wkt), pressure is critical compared to 60 runs needed with 8 wickets in hand (\(7.5\) runs/wkt).
4. **Death-Overs Closeness Multiplier**:
   - In the final 5 overs (\(\text{balls\_remaining} \le 30\)), situational leverage multiplies raw tension, scaling pressure as the match approaches its climax.

---

## 4. Normalization and Pressure Tiers

Raw composite indices are mapped to a continuous **0–100 scale** via a calibrated logistic sigmoid transformation:
\[
\text{Pressure Score} = \frac{100}{1 + e^{-k \cdot (\text{Raw} - x_0)}}
\]

### Pressure Tiers
- **Low (0–25)**: Comfortable match states (e.g. powerplay with 0 wickets down, or chasing at < 6.5 RPO).
- **Moderate (25–50)**: Standard competitive T20 match states (e.g. middle overs around 8 RPO).
- **High (50–75)**: Elevated tension (e.g. RRR 9–12 RPO, or 4 wickets lost in 1st innings).
- **Very High (75–90)**: Acute pressure (e.g. RRR 12–15 RPO, tail exposed).
- **Extreme (90–100)**: Climax crisis states (e.g. >15 RPO needed, 1 wicket left, or Super Overs).

---

## 5. Super Overs Handling

Super overs represent instantaneous sudden-death scenarios. Every delivery is assigned an extreme baseline pressure of **90.0–95.0**, scaling with wickets in hand, while remaining excluded from regular T20 career averages.
