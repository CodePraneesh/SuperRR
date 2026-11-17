# SupeRR Intelligence: Uniform Minimum-Evidence Floor Rule (≥ 250 Pressure Deliveries)

**Author:** SupeRR Intelligence Research & Engineering Team  
**Date:** November 17, 2026  
**Status:** Post-Hoc Methodological Enhancement (Explicitly Disclosed)  
**Scope:** Official Top 10 Rankings Selection (Batters & Bowlers)  

---

## 1. Rule Specification & Formal Declaration

Under the uniform minimum-evidence rule:
1. **Eligibility Criterion:** A player is rank-eligible for inclusion in the official Top 10 rankings if and only if they have faced or bowled at least **250 pressure deliveries** ($\ge 250$ legal balls) in the evaluated role (striker for batters, bowler for bowlers) within the in-scope competition dataset (IPL + Senior Men's T20I, excluding Emerging Teams).
2. **Pressure Demarcation Retained:** The high-pressure situation definition remains strictly the pre-delivery Pressure Index benchmark ($PI \ge 50.0$) formulated prior to delivery execution.
3. **Core Scoring Invariance:** The Cricket Pressure-Performance Reliability Index (CPRI) mathematical formulation, weights, components (Pressure Impact 40%, Adaptability 25%, Consistency 20%, Reliability 15%), and individual player CPRI scores remain **100% unchanged**. Zero scores are recalculated, boosted, or penalized.
4. **Rank Re-Numbering:** Eligible players ($\ge 250$ pressure balls) are sorted by their existing, immutable Phase 8 CPRI score descending, and ranks are re-numbered $1, 2, \dots, N$.
5. **Algorithmic Uniformity:** The rule is applied mechanically across all 1,280 tracked players with zero hardcoded player names, zero manual exemptions, and zero outside facts.

---

## 2. Explicit Post-Hoc Disclosure & Methodological Justification

> **CRITICAL DISCLOSURE**: This minimum-evidence floor ($\ge 250$ balls) is a **POST-HOC methodological decision**. It was formulated and implemented following thorough empirical examination of the frozen Phase 8 leaderboards and uncertainty profiles. It was **NOT pre-registered** prior to observing leaderboard compositions.

### 2.1 Why a 250-Ball Floor Is Necessary
In the frozen Phase 8 baseline (which enforced an initial technical floor of 120 pressure deliveries):
- **Sufiyan Muqeem** (#2 Bowler, CPRI 78.78) accumulated only 151 pressure balls across 11 matches, yielding an exceptionally wide 90% bootstrap rank interval of **[1, 74]** (standard deviation $\sigma = 23.92$).
- **Jamie Overton** (#4 Bowler, CPRI 76.92) accumulated only 168 pressure balls across 14 matches, resulting in a 90% rank interval of **[1, 71]** ($\sigma = 23.62$).
- **Matthew Wade** (#1 Batter, CPRI 85.36) accumulated 191 pressure balls across 15 matches with a 90% rank interval of **[1, 22]** ($\sigma = 9.88$).

While Bayesian shrinkage shrinks low-sample rates toward the league prior, rank ordering at the extreme tails remains sensitive to high rate variances over short samples ($\le 200$ balls). Requiring $\ge 250$ pressure deliveries ensures:
- Sufficient match diversity and opposition variety across multiple seasons or tournaments.
- Stabilization of 90% bootstrap rank confidence intervals.
- The official dropdown submission represents robust, battle-tested performers rather than short-sample rate outliers.

---

## 3. Floor Sensitivity Analysis (Floors: 150, 200, 250, 300, 400 Balls)

The following tables demonstrate the exact empirical behavior of the Top 10 leaderboards under alternative minimum-evidence thresholds. All scores and delivery counts are derived programmatically from the frozen `batter_full_population.csv` and `bowler_full_population.csv`.

### 3.1 Batters Leaderboard Sensitivity Across Evidence Floors

| Rank | Floor $\ge 150$ (Phase 8 Baseline) | Floor $\ge 200$ | Floor $\ge 250$ (Adopted Rule) | Floor $\ge 300$ | Floor $\ge 400$ |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **#1** | Matthew Wade (191b, 85.36) | Tim David (476b, 82.44) | **Tim David** (476b, 82.44) | Tim David (476b, 82.44) | Tim David (476b, 82.44) |
| **#2** | Tim David (476b, 82.44) | Suryakumar Yadav (749b, 81.42) | **Suryakumar Yadav** (749b, 81.42) | Suryakumar Yadav (749b, 81.42) | Suryakumar Yadav (749b, 81.42) |
| **#3** | Suryakumar Yadav (749b, 81.42) | Reeza Hendricks (378b, 77.45) | **Reeza Hendricks** (378b, 77.45) | Reeza Hendricks (378b, 77.45) | Rinku Singh (457b, 77.18) |
| **#4** | Reeza Hendricks (378b, 77.45) | Rinku Singh (457b, 77.18) | **Rinku Singh** (457b, 77.18) | Rinku Singh (457b, 77.18) | Romario Shepherd (428b, 75.33) |
| **#5** | Rinku Singh (457b, 77.18) | Phil Salt (261b, 76.96) | **Phil Salt** (261b, 76.96) | Romario Shepherd (428b, 75.33) | Tilak Varma (777b, 74.81) |
| **#6** | Phil Salt (261b, 76.96) | Romario Shepherd (428b, 75.33) | **Romario Shepherd** (428b, 75.33) | Tilak Varma (777b, 74.81) | Ravindra Jadeja (467b, 73.70) |
| **#7** | Romario Shepherd (428b, 75.33) | Tilak Varma (777b, 74.81) | **Tilak Varma** (777b, 74.81) | Ravindra Jadeja (467b, 73.70) | Ayush Badoni (416b, 69.60) |
| **#8** | Tilak Varma (777b, 74.81) | Dinesh Karthik (277b, 74.54) | **Dinesh Karthik** (277b, 74.54) | Shashank Singh (327b, 72.83) | Tristan Stubbs (579b, 69.55) |
| **#9** | Dinesh Karthik (277b, 74.54) | Ravindra Jadeja (467b, 73.70) | **Ravindra Jadeja** (467b, 73.70) | MS Dhoni (360b, 69.85) | Dasun Shanaka (402b, 68.70) |
| **#10** | Ravindra Jadeja (467b, 73.70) | Shashank Singh (327b, 72.83) | **Shashank Singh** (327b, 72.83) | Ayush Badoni (416b, 69.60) | Nicholas Pooran (673b, 68.43) |

- **Key Transition at 250 Balls**: Matthew Wade (191 balls) drops out; Tim David ascends to #1; Shashank Singh (327 balls, CPRI 72.83, formerly #11) enters at #10.
- **Ranks 2–9 under Phase 8**: Each advance exactly 1 position without changing relative sequence.

---

### 3.2 Bowlers Leaderboard Sensitivity Across Evidence Floors

| Rank | Floor $\ge 150$ (Phase 8 Baseline) | Floor $\ge 200$ | Floor $\ge 250$ (Adopted Rule) | Floor $\ge 300$ | Floor $\ge 400$ |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **#1** | Mitchell Santner (653b, 79.84) | Mitchell Santner (653b, 79.84) | **Mitchell Santner** (653b, 79.84) | Mitchell Santner (653b, 79.84) | Mitchell Santner (653b, 79.84) |
| **#2** | Sufiyan Muqeem (151b, 78.78) | Rashid Khan (970b, 77.90) | **Rashid Khan** (970b, 77.90) | Rashid Khan (970b, 77.90) | Rashid Khan (970b, 77.90) |
| **#3** | Rashid Khan (970b, 77.90) | Matheesha Pathirana (557b, 75.77) | **Matheesha Pathirana** (557b, 75.77) | Matheesha Pathirana (557b, 75.77) | Matheesha Pathirana (557b, 75.77) |
| **#4** | Jamie Overton (168b, 76.92) | Sunil Narine (511b, 75.63) | **Sunil Narine** (511b, 75.63) | Sunil Narine (511b, 75.63) | Sunil Narine (511b, 75.63) |
| **#5** | Matheesha Pathirana (557b, 75.77) | Mohammad Nawaz (301b, 75.51) | **Mohammad Nawaz** (301b, 75.51) | Mohammad Nawaz (301b, 75.51) | Jasprit Bumrah (606b, 73.36) |
| **#6** | Sunil Narine (511b, 75.63) | Jasprit Bumrah (606b, 73.36) | **Jasprit Bumrah** (606b, 73.36) | Jasprit Bumrah (606b, 73.36) | Varun Chakravarthy (892b, 73.02) |
| **#7** | Mohammad Nawaz (301b, 75.51) | Varun Chakravarthy (892b, 73.02) | **Varun Chakravarthy** (892b, 73.02) | Varun Chakravarthy (892b, 73.02) | Yuzvendra Chahal (859b, 73.01) |
| **#8** | Jasprit Bumrah (606b, 73.36) | Yuzvendra Chahal (859b, 73.01) | **Yuzvendra Chahal** (859b, 73.01) | Yuzvendra Chahal (859b, 73.01) | Mustafizur Rahman (527b, 72.12) |
| **#9** | Varun Chakravarthy (892b, 73.02) | Abrar Ahmed (291b, 72.93) | **Abrar Ahmed** (291b, 72.93) | Mustafizur Rahman (527b, 72.12) | Wanindu Hasaranga (639b, 71.86) |
| **#10** | Yuzvendra Chahal (859b, 73.01) | Mohit Sharma (282b, 72.71) | **Mohit Sharma** (282b, 72.71) | Wanindu Hasaranga (639b, 71.86) | Kuldeep Yadav (627b, 71.29) |

- **Key Transition at 250 Balls**: Sufiyan Muqeem (151 balls) and Jamie Overton (168 balls) drop out.
- **Top 4 Retention**: Mitchell Santner retains #1 (653 balls); Rashid Khan ascends to #2 (970 balls); Matheesha Pathirana moves to #3 (557 balls); Sunil Narine moves to #4 (511 balls).
- **New Entrants**: Abrar Ahmed (291 balls, CPRI 72.93, formerly #11) enters at #9; Mohit Sharma (282 balls, CPRI 72.71, formerly #12) enters at #10.

---

## 4. Preservation of Pre-Floor Baseline
To maintain complete scientific and audit transparency:
- The authoritative Phase 8 lists (`output/phase8_ranking_reconsideration/`) remain permanently preserved and cryptographically sealed under the `phase8-frozen-pre-evidence-floor` tag.
- In all reporting, dashboards, and APIs, the Phase 8 lists will be accessible as the **"Pre-Floor Baseline (Phase 8 Frozen)"** view, ensuring reviewers can inspect both the raw unconstrained model outputs and the stabilized minimum-evidence floor selections.
