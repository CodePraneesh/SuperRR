# SupeRR Intelligence — Phase 2A: Dynamic Pressure Detection Engine Validation Report

**Prepared by**: Senior Cricket Analytics Engineer & ML Researcher  
**Date**: November 12, 2026  
**Pipeline**: Phase 2A Dynamic Pressure Detection Engine  
**Dataset Scope**: Indian Premier League (IPL) & Twenty20 International (T20I)  
**Deliverable Outputs**:
- \ml/phase2/pressure_features.py\
- \ml/phase2/pressure_engine.py\
- \ml/phase2/pressure_validation.py\
- \output/phase2/pressure_scored_deliveries.csv\
- \output/phase2/pressure_distribution.csv\
- \output/phase2/pressure_assumptions.md\
- \output/phase2/pressure_validation_report.md\
- \	ests/test_pressure_engine.py\

---

## 1. Executive Summary

Phase 2A delivers a mathematically rigorous, ML-grounded **Dynamic Pressure Detection Engine** that computes a normalized contextual pressure index (0 to 100) for every ball bowled in IPL and T20I matches. 

The engine evaluates contextual difficulty, match tension, and resource leverage strictly using information available **prior to the delivery being bowled**. It replaces heuristic multipliers with an empirical **Historical Expected-Remaining-Runs Model** for the first innings and an empirical **Win-Leverage Resource Deficit Model** for the second innings.

### Key Technical Achievements
1. **Zero Future & Zero Current-Ball Leakage**: Verified that no delivery outcome, final match score, or post-ball event leaks into model inputs.
2. **First-Innings Par Deficit Grounding**: Integrated a chronological Gradient Boosting model to forecast expected innings totals (\(R^2 = 0.8014\)), measuring batting/bowling pressure against format benchmark pars (186 for IPL, 171 for T20I).
3. **Chasing Pressure Strongly Predicts Outcomes**: Deliveries classified in the **Low Pressure Tier** exhibit a **91.2%** chasing team win rate, dropping monotonically to **28.2%** in High Pressure, and **2.0%** in Extreme Pressure.
4. **100% Automated Unit Test Pass Rate**: 10 out of 10 unit tests passed without errors.

---

## 2. Pressure Metric Architecture

### 2.1 First-Innings Pressure Formulation
In the first innings, teams face resource-depletion tension against a competitive par total:
\[
P_{\text{1st}} = \sigma \Big( 0.35 \cdot \text{ParDeficit} + 0.35 \cdot \text{WicketScarcity} + 0.20 \cdot \text{PhaseUrgency} + 0.10 \cdot \text{RunRateDrag} \Big)
\]
- **Expected Remaining Runs Model**: Trained using \HistGradientBoostingRegressor\ across 843 completed 1st innings. Chronological test validation demonstrated:
  - **Mean Absolute Error (MAE)**: 18.38 runs
  - **Root Mean Squared Error (RMSE)**: 25.53 runs
  - **Out-of-Sample \(R^2\)**: **0.8014**
- **Format Benchmark Par**: Grounded in historical averages: 186.7 for IPL, 171.2 for T20I.

### 2.2 Second-Innings (Chasing) Pressure Formulation
In the chase, pressure is a direct function of instantaneous resource requirements:
\[
P_{\text{Chase}} = \sigma \Big( \big[ 0.45 \cdot \text{RRR\_S\_Curve} + 0.30 \cdot \text{BallDeficit} + 0.25 \cdot \text{RunsPerWicket} \big] \cdot \text{DeathLeverage} \Big)
\]
- **Required Run Rate**: Modeled via a hyperbolic tangent transform: \(\tanh((\text{RRR}/14.0)^{1.3})\).
- **Death Closeness Multiplier**: Final 5 overs (\(\le 30\) balls remaining) amplify pressure up to \(1.5\times\) as margin for error vanishes.

---

## 3. Empirical Distribution Analysis

Analysis of 194,014 official-scope deliveries in \output/phase2/pressure_distribution.csv\:

| Segment | Category | Deliveries | Mean Score | Median Score | P25 | P75 | P90 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Overall** | All In-Scope | 194,014 | **37.31** | **31.42** | 12.56 | 57.49 | 77.41 |
| **Format** | IPL | 87,687 | **38.71** | **33.63** | 13.80 | 59.94 | 77.42 |
| **Format** | T20I | 106,327 | **36.14** | **29.46** | 11.77 | 55.06 | 77.40 |
| **Innings** | Innings 1 (Setting) | 102,054 | **25.46** | **16.72** | 9.60 | 34.12 | 59.46 |
| **Innings** | Innings 2 (Chasing) | 91,934 | **50.44** | **50.76** | 31.07 | 68.89 | 85.48 |
| **Phase** | Powerplay (Overs 1–6) | 61,774 | **30.04** | **21.70** | 8.73 | 49.19 | 64.27 |
| **Phase** | Middle (Overs 7–15) | 89,458 | **35.25** | **28.52** | 12.48 | 55.27 | 73.25 |
| **Phase** | Death (Overs 16–20) | 42,756 | **52.07** | **45.79** | 26.14 | 80.82 | 94.41 |
| **Phase** | Super Over | 26 | **90.35** | **90.00** | 90.00 | 91.00 | 91.00 |
| **Wickets Left** | Top Order (7–10 wkts) | 131,246 | **28.31** | **19.94** | 10.20 | 44.41 | 61.98 |
| **Wickets Left** | Middle Order (4–6 wkts) | 49,847 | **49.81** | **48.23** | 29.47 | 70.20 | 82.64 |
| **Wickets Left** | Tailenders (1–3 wkts) | 12,921 | **80.48** | **87.19** | 74.46 | 94.55 | 98.17 |
| **Chase RRR** | Low (<6.0 RPO) | 12,678 | **11.82** | **11.84** | 8.72 | 14.56 | 16.75 |
| **Chase RRR** | Normal (6.0–9.0 RPO) | 26,877 | **33.63** | **34.09** | 26.97 | 40.26 | 44.95 |
| **Chase RRR** | High (9.0–12.0 RPO) | 30,453 | **57.88** | **57.68** | 51.54 | 64.17 | 68.82 |
| **Chase RRR** | Severe (12.0–15.0 RPO) | 11,484 | **75.43** | **75.57** | 70.83 | 80.24 | 83.54 |
| **Chase RRR** | Extreme (>15.0 RPO) | 8,919 | **90.21** | **91.01** | 86.67 | 94.91 | 97.03 |

---

## 4. Pressure Score vs Match Outcomes

A critical validation of contextual validity is how pressure relates to empirical match victory. In the second innings, delivery pressure reflects the chasing team's probability of defeat:

| Pressure Tier | Score Range | Deliveries | Chasing Team Win Rate | Interpretation |
|:---|:---:|:---:|:---:|:---|
| **Low** | 0.0 – 25.0 | 17,953 | **91.22%** | Dominant chase; cruise control. |
| **Moderate** | 25.0 – 50.0 | 26,994 | **67.66%** | Evenly matched / slight advantage to chasing team. |
| **High** | 50.0 – 75.0 | 29,917 | **28.21%** | Batting team under serious pressure; bowling team in control. |
| **Very High** | 75.0 – 90.0 | 10,466 | **5.65%** | Acute crisis; boundary boundary required. |
| **Extreme** | 90.0 – 100.0 | 6,604 | **2.00%** | Near-impossible rescue required; bowler heavily favoured. |

> **Monotonicity Confirmation**: As pressure increases from Low to Extreme, chasing team win probability drops strictly monotonically from **91.2% down to 2.0%**.

---

## 5. Automated Unit Tests

Executed via: \python -m unittest -v tests/test_pressure_engine.py\

| Test ID | Test Name | Target Rule / Specification | Status | Time |
|:---|:---|:---|:---:|:---:|
| **T01** | \	est_01_pressure_score_bounds\ | Pressure scores strictly bounded between 0.0 and 100.0 | **PASSED** | 0.04s |
| **T02** | \	est_02_no_future_leakage_in_features\ | Pre-delivery state has zero lookahead leakage | **PASSED** | 0.48s |
| **T03** | \	est_03_first_and_second_innings_distinguishable\ | 1st innings and chasing metrics are kept distinguishable | **PASSED** | 0.22s |
| **T04** | \	est_04_chase_monotonic_with_required_run_rate\ | Pressure scales monotonically with Required Run Rate | **PASSED** | 0.08s |
| **T05** | \	est_05_wickets_scarcity_impact\ | Tailenders face higher pressure than top order | **PASSED** | 0.06s |
| **T06** | \	est_06_phase_progression\ | Death overs exhibit higher pressure than powerplay | **PASSED** | 0.06s |
| **T07** | \	est_07_super_over_highest_pressure\ | Super Overs categorized in extreme pressure tier (>=85) | **PASSED** | 0.01s |
| **T08** | \	est_08_emerging_teams_exclusion_flag\ | Emerging Teams correctly flagged as out-of-scope | **PASSED** | 0.02s |
| **T09** | \	est_09_unlabelled_extras_isolated\ | Unlabelled extras remain isolated and non-legal | **PASSED** | 0.02s |
| **T10** | \	est_10_match_outcome_relationship\ | Chasing win rate decreases monotonically with pressure | **PASSED** | 0.24s |

**Summary**: 10 Passed, 0 Failed, 0 Errors. Total Test Time: 7.10s.

---

## 6. Documented Remaining Warnings & Monitoring

1. **20 Four-Flag & 3 Six-Flag Discrepancies**: Raw boundary flags disagree with runs scored on 23 rows. Resolved via derived flags \derived_four = (runs == 4)\ and \derived_six = (runs == 6)\.
2. **2 Unlabelled Non-Zero Extras**: Flagged as \unlabelled_extras\; isolated from legal deliveries and bowler concessions.
3. **40 Playing XI Duplicates & 83 Unmapped Strikers**: Handled through diagnostic deduplication and source-name fallbacks. Impact player substitutions explain these anomalies.
4. **40 Abandoned/Incomplete Matches**: Strictly excluded from the training target of the historical expected-remaining-runs model.

---

## 7. Readiness Declaration

> **OFFICIAL STATUS: PHASE 2A IS VALIDATED, TESTED, AND READY FOR PHASE 2B.**
>
> With delivery-level contextual pressure scores rigorously calculated and verified against actual match outcomes, the foundation is set to compute context-adjusted player expectations and clutchness ratings in Phase 2B.
