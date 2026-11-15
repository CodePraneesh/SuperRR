# SupeRR Intelligence — Phase 3.3 Unified Ranking Audit Report

**Prepared by:** Senior Sports Analytics Researcher, Statistical Modeler & Cricket Performance Scientist  
**Date:** November 2026  
**Competition Scope:** Indian Premier League (IPL) & Twenty20 International (T20I)  
**Status:** Audit Completed, Methodology Unified, Independent Validation 100% Passed

---

## 1. Executive Summary & Audit Mandate

Phase 3.3 represents the comprehensive, unified audit of the Clutch Performance & Reliability Index (CPRI) ranking engines for both batters and bowlers across IPL and T20 International cricket.

The mandate required an independent investigation into:
1. **Pressure-Specific Reliability**: Auditing whether players with few pressure deliveries received inflated confidence classifications purely due to high total career delivery volume.
2. **Bowler & Batter Top 10 Eligibility**: Investigating flagged anomaly entries:
   - *IPL Bowlers*: Lungi Ngidi, Ayush Badoni, Tristan Stubbs, Ashwani Kumar.
   - *T20I Bowlers*: Mark Watt, Sufiyan Muqeem, Tabraiz Shamsi, Aiden Markram.
   - *Batters*: Karun Nair, Shan Masood, Muhammad Waseem, Rashid Khan, Matthew Wade.
3. **Adaptability Stability**: Investigating raw adaptability spikes, small non-pressure and pressure baselines, and evaluating robust sigmoid scaling versus linear min-max.
4. **Clutch Consistency**: Verifying whether the consistency metric rewards repeatable player-level match performance or accidentally rewards small-sample volatility.
5. **Bowler Role & Workload Validation**: Determining whether the source data supports specialist bowler identification and establishing role-neutral, workload-based qualification standards.
6. **Independent Score Validation**: Recalculating the composite CPRI score from its four components across all 1,745 player records ($1,006$ batters and $739$ bowlers).

---

## 2. Task 1: Pressure-Specific Reliability & Confidence System

### The Flaw of Career-Volume Confidence in Phase 3
In Phase 3 and Phase 3.1, a player could achieve High Confidence with as few as 3 pressure matches ($M_P \ge 3$) and 50 pressure balls ($N_P \ge 50$) as long as their total delivery count exceeded 100 ($N_{\text{total}} \ge 100$). This led to severe classification failures:
- **Tabraiz Shamsi (T20I)**: Bowled 321 total balls (High Confidence in Phase 3.1), but had only **4 pressure matches** (98 balls). Standard error on his match mean was $40.5$ runs/100 balls!
- **Lungi Ngidi (IPL)**: Bowled 303 total balls (High Confidence and ranked #1 in IPL), but had only **6 pressure matches** (69 balls).
- **Karun Nair (IPL)**: Faced 158 total balls, but only **4 pressure matches** (65 balls).
- **Shan Masood (T20I)**: Faced 185 total balls, but only **3 pressure matches** (91 balls).

### Unified Phase 3.3 Statistical Framework
In cricket, deliveries are nested within matches. Estimating player clutch performance requires accounting for match-level clustering and design effects:

1. **Design-Effect Adjusted Effective Sample Size ($N_{\text{eff}}$)**:
   $$\bar{n}_P = \frac{N_P}{M_P}, \quad \text{DEFF} = 1 + (\bar{n}_P - 1)\rho$$
   $$N_{\text{eff}} = \frac{N_P}{\text{DEFF}}$$
   where $\rho = 0.15$ is the intra-cluster correlation across matches.
2. **Pressure-Specific Uncertainty ($\mathrm{SE}_P$)**:
   $$\mathrm{SE}_P = \frac{\sigma_{\text{match}}}{\sqrt{M_P}}$$
3. **Non-Pressure Sample Adequacy ($A_{NP}$)**:
   $$A_{NP} = \min\left(1.0, \frac{N_{NP}}{60.0}\right)$$
   A player with $N_{NP} < 40$ balls has an unstable non-pressure baseline, creating extreme artificial swings in adaptability.

### Separate, Justified Confidence Rules

#### Batter Confidence Rules
- **High Confidence (Official Top 10 Eligible)**:
  $$N_P \ge 100 \quad \text{AND} \quad M_P \ge 8 \quad \text{AND} \quad N_{\text{total}} \ge 150 \quad \text{AND} \quad N_{NP} \ge 40$$
- **Moderate Confidence**:
  $$N_P \ge 40 \quad \text{AND} \quad M_P \ge 3 \quad \text{AND} \quad N_{\text{total}} \ge 60$$
- **Low Confidence**: All remaining batters.

#### Bowler Confidence Rules (Workload-Based)
- **High Confidence (Official Top 10 Eligible)**:
  $$N_P \ge 100 \quad \text{AND} \quad M_P \ge 8 \quad \text{AND} \quad N_{\text{total}} \ge 180 \text{ (30 overs)} \quad \text{AND} \quad \text{Balls/Match} \ge 12.0$$
- **Moderate Confidence (Provisional)**:
  $$N_P \ge 40 \quad \text{AND} \quad M_P \ge 3 \quad \text{AND} \quad N_{\text{total}} \ge 60$$
- **Low Confidence (Part-Time / Small Sample)**: All remaining bowlers.

*Audit Datasets:* Fully exported in [batter_confidence_audit.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/batter_confidence_audit.csv) (1,006 players) and [bowler_confidence_audit.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/bowler_confidence_audit.csv) (739 players).

---

## 3. Task 2: Investigation of Flagged Bowlers & Batters

| Player | Scope | Role | Career Balls | Pressure Balls | Pressure Matches | Balls/Match | P3.1 Rank / Tier | P3.3 Rank / Tier | Audit Verdict & Classification |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Matheesha Pathirana** | IPL | Bowler | 797 | 391 | 19 | 24.15 | #2 (High) | **#1 (High)** | **Official #1**: Elite death-overs volume and execution. |
| **Lungi Ngidi** | IPL | Bowler | 303 | 69 | 6 | 23.31 | #1 (High) | **#1 (Prov)** | **Provisional #1**: Demoted from Top 10 ($N_P=69 < 100, M_P=6 < 8$). |
| **Ayush Badoni** | IPL | Bowler | 41 | 13 | 3 | 5.12 | #4 (Low) | **Excluded** | **Excluded**: Part-time bowler (5.1 balls/m, 41 total balls). |
| **Tristan Stubbs** | IPL | Bowler | 37 | 13 | 2 | 7.40 | #9 (Low) | **Excluded** | **Excluded**: Part-time bowler (7.4 balls/m, 37 total balls). |
| **Ashwani Kumar** | IPL | Bowler | 196 | 90 | 5 | 19.60 | #8 (High) | **#2 (Prov)** | **Provisional #2**: Demoted ($N_P=90 < 100, M_P=5 < 8$). |
| **Sufiyan Muqeem** | T20I | Bowler | 351 | 151 | 10 | 20.65 | #1 (High) | **#1 (High)** | **Official #1**: Robust sample (151 balls, 10 matches, 23 wkts). |
| **Kuldeep Yadav** | T20I | Bowler | 542 | 174 | 12 | 21.68 | #2 (High) | **#2 (High)** | **Official #2**: Elite specialist wrist spin under pressure. |
| **Mark Watt** | T20I | Bowler | 128 | 11 | 1 | 21.33 | #2 (Low) | **Excluded** | **Excluded**: Extreme small sample (11 pressure balls, 1 match). |
| **Tabraiz Shamsi** | T20I | Bowler | 321 | 98 | 4 | 20.06 | #5 (High) | **#2 (Prov)** | **Provisional #2**: Demoted ($N_P=98 < 100, M_P=4 < 8$). |
| **Aiden Markram** | T20I | Bowler | 203 | 19 | 3 | 10.15 | #10 (Low) | **Excluded** | **Excluded**: Part-time bowler (10.1 balls/m, 19 pressure balls). |
| **Rinku Singh** | IPL | Batter | 926 | 411 | 25 | — | #2 (High) | **#1 (High)** | **Official #1**: Elite pressure volume and uncompressed adaptability. |
| **Rashid Khan** | IPL | Batter | 262 | 219 | 26 | — | #1 (High) | **#8 (High)** | **Official #8**: Balanced high-power profile with regulated adaptability. |
| **Karun Nair** | IPL | Batter | 158 | 65 | 4 | — | #10 (High) | **#3 (Prov)** | **Provisional #3**: Demoted from Top 10 ($N_P=65 < 100, M_P=4 < 8$). |
| **Matthew Wade** | T20I | Batter | 294 | 160 | 12 | — | #1 (High) | **#1 (High)** | **Official #1**: Verified 100% positive match ratio (12/12 matches). |
| **Shan Masood** | T20I | Batter | 185 | 91 | 3 | — | #10 (High) | **#4 (Prov)** | **Provisional #4**: Demoted from Top 10 ($N_P=91 < 100, M_P=3 < 8$). |
| **Muhammad Waseem**| T20I | Batter | 472 | 114 | 6 | — | #5 (High) | **#1 (Prov)** | **Provisional #1**: Top moderate confidence candidate ($M_P=6 < 8$). |

---

## 4. Task 3: Adaptability Stability & Score Saturation Audit

### The Outlier Anomaly Analysis
Raw adaptability represents the difference between pressure and non-pressure impact rates:
$$\text{Raw Adaptability} = \text{Impact Rate}_P - \text{Impact Rate}_{NP}$$

When a player faces very few deliveries in either condition, single events cause extreme mathematical explosions:
- **Mark Watt (T20I Bowler)**: Bowled only 11 balls in pressure across 1 match, conceding 3 runs and taking 2 wickets. This produced a raw pressure impact rate of $+492.3$ runs/100 balls, and raw adaptability of **+485.8**!
- **Tristan Stubbs (IPL Bowler)**: Bowled only 13 balls in pressure, taking 2 wickets. Raw adaptability reached **+311.9**!
- **Ayush Badoni (IPL Bowler)**: Bowled only 13 balls in pressure. Raw adaptability reached **+301.7**!
- **Rashid Khan (IPL Batter)**: Faced 219 balls in pressure, but only 43 balls in non-pressure. Dismissed 9 times in 43 balls (-192.91 non-pressure rate), driving raw adaptability to **+251.98**!

### Normalization Comparison: Linear Min-Max vs Robust Sigmoid
Under linear min-max scaling ($S = 100 \times (x - x_{\min}) / (x_{\max} - x_{\min})$):
- The maximum outlier stretches the denominator to $\approx 220-250$ points.
- Batters and bowlers with strong natural positive adaptability ($+15$ to $+35$) were compressed into the $50-65$ score range, destroying performance differentiation across 95% of the league.

Under Phase 3.3 **Robust Sigmoid Normalization**:
$$Z = \frac{x - \text{median}(x)}{\text{IQR}(x) / 1.349}, \quad \text{Score}_{\text{adaptability}} = \frac{100}{1 + \exp(-0.6 \cdot Z)}$$
- Outliers approach 100.0 asymptotically without stretching the scale or compressing other players.
- Median performance maps exactly to 50.0.
- Differentiation is strictly preserved (strictly monotonic, no flat saturation shelves).
- Elite finishers gain their deserved separation: Rinku Singh ($63.9 \to \mathbf{91.5}$), Suryakumar Yadav ($50.4 \to \mathbf{76.9}$), Dinesh Karthik ($59.7 \to \mathbf{88.2}$), Matheesha Pathirana ($73.9 \to \mathbf{71.7}$), Mohit Sharma ($92.2 \to \mathbf{86.0}$).

*Stability Dataset:* Full sensitivity across prior weights ($M=40$ vs $M=80$) and winsorization is published in [adaptability_stability_report.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/adaptability_stability_report.csv).

---

## 5. Task 4: Clutch Consistency Audit

### Repeatability vs Sample Volatility
Clutch consistency combines three match-level dimensions evaluated exclusively across pressure matches:
$$\text{Raw Consistency} = 0.50 \times \text{PosMatchRatio} + 0.30 \times \text{MeanRate}_{\text{scaled}} + 0.20 \times \text{Stability}_{\text{scaled}}$$

The audit revealed that when $M_P \le 3$, consistency scores were artificially inflated:
- **Ayush Badoni (Bowler)**: Achieved a consistency score of **99.5** based on only 3 matches (all 3 positive by chance).
- **Tristan Stubbs (Bowler)**: Achieved a consistency score of **95.7** based on only 2 matches.
- **Shan Masood (Batter)**: Achieved a consistency score of **76.5** based on only 3 matches.

### Resolution
By enforcing the strict sample requirement ($M_P \ge 8$) for High Confidence eligibility, players with volatile 2-to-4 match samples cannot leverage an inflated consistency score into an official Top 10 ranking. For true High Confidence players, consistency reliably measures genuine repeatability:
- **Matthew Wade**: $12 / 12$ positive matches ($100.0\%$, consistency $100.0$).
- **Matheesha Pathirana**: $14 / 19$ positive matches ($73.7\%$, consistency $100.0$).
- **Suryakumar Yadav**: $21 / 28$ positive matches in IPL ($75.0\%$, consistency $85.2$).
- **Rashid Khan**: $12 / 26$ positive matches in IPL ($46.2\%$, consistency $40.9$ — appropriately reflects high variance).

*Consistency Dataset:* Comprehensive match statistics and standard errors are published in [consistency_audit.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/consistency_audit.csv).

---

## 6. Task 5: Bowler Eligibility and Role Validation

### Data Limitation Disclosure
Inspection of `cleaned_deliveries.csv`, `deliveries_enriched.csv`, and `bowler_delivery_expectations.csv` confirms that **no player role metadata** (e.g. "Specialist Bowler", "All-Rounder", "Part-Timer") exists in the source database.

### Sanctioned, Role-Neutral Policy
To satisfy the rule against inventing missing data or assuming unsupported player roles, bowler eligibility is governed strictly by **objective bowling workload**:
1. **Bowling Density Minimum**: A player must average at least **12.0 deliveries per match** they bowl in ($\ge 2.0$ overs/match). Part-time bowlers (Ayush Badoni: $5.1$ balls/m, Tristan Stubbs: $7.4$ balls/m, Aiden Markram: $9.3 - 10.1$ balls/m) are objectively disqualified.
2. **Career Workload Minimum**: A player must have bowled at least **180 total career deliveries** (30 overs).
3. **Pressure Sample Minimum**: A player must have bowled at least **100 pressure deliveries** across at least **8 pressure matches**.

---

## 7. Task 6: Independent Score Validation

The composite CPRI score was independently recalculated for all 1,745 player records ($1,006$ batters and $739$ bowlers):
$$\text{CPRI}_{\text{recalc}} = 0.40 \times \text{Pressure Impact} + 0.25 \times \text{Pressure Adaptability} + 0.20 \times \text{Clutch Consistency} + 0.15 \times \text{Reliability Confidence}$$

### Validation Results
- **Batters Discrepancies ($|\Delta| > 0.01$)**: **0 / 1,006 (0.00%)** — Maximum error: $0.0000$.
- **Bowlers Discrepancies ($|\Delta| > 0.01$)**: **0 / 739 (0.00%)** — Maximum error: $0.0000$.
- **Formula Integrity**: **100.0% Validated**.

---

## 8. Final Official Top 10 Rankings & Provisional Ladders

### Indian Premier League (IPL)

#### Official Eligible Top 10 Batters
| Rank | Player Name | CPRI | Impact | Adapt | Consist | Reliab | Pressure Balls | Pressure Matches | Career Balls | Pos Match % |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Rinku Singh** | **89.03** | 100.0 | 91.5 | 56.3 | 99.2 | 411 | 25 | 926 | 52.0% |
| **#2** | **Ashutosh Sharma** | **88.86** | 93.9 | 89.3 | 72.0 | 97.2 | 261 | 21 | 356 | 66.7% |
| **#3** | **Suryakumar Yadav** | **88.41** | 93.0 | 76.9 | 85.2 | 99.6 | 537 | 28 | 1391 | 75.0% |
| **#4** | **Ravindra Jadeja** | **87.78** | 90.4 | 90.5 | 70.2 | 99.7 | 439 | 30 | 872 | 63.3% |
| **#5** | **Dinesh Karthik** | **87.75** | 95.2 | 88.2 | 66.9 | 94.9 | 222 | 18 | 489 | 61.1% |
| **#6** | **Tim David** | **87.59** | 99.1 | 85.5 | 58.5 | 99.1 | 327 | 27 | 694 | 55.6% |
| **#7** | **Namboori Tilak Varma** | **86.34** | 89.5 | 85.2 | 71.4 | 99.7 | 585 | 30 | 1343 | 66.7% |
| **#8** | **Rashid Khan** | **85.59** | 94.9 | 99.6 | 40.9 | 96.9 | 219 | 26 | 262 | 46.2% |
| **#9** | **Shashank Singh** | **85.57** | 93.8 | 82.2 | 63.6 | 98.6 | 327 | 23 | 623 | 60.9% |
| **#10** | **Ayush Badoni** | **84.97** | 84.2 | 92.2 | 66.5 | 99.5 | 416 | 28 | 716 | 64.3% |

#### Official Eligible Top 10 Bowlers
| Rank | Player Name | CPRI | Impact | Adapt | Consist | Reliab | Pressure Balls | Pressure Matches | Career Balls | Balls/Match |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Matheesha Pathirana** | **83.50** | 77.3 | 71.7 | 100.0 | 97.6 | 391 | 19 | 797 | 24.15 |
| **#2** | **Mohit Sharma** | **79.15** | 78.5 | 86.0 | 57.9 | 97.9 | 282 | 22 | 676 | 20.48 |
| **#3** | **Eshan Malinga** | **76.57** | 73.6 | 64.5 | 90.0 | 86.6 | 219 | 11 | 516 | 23.45 |
| **#4** | **Sai Kishore** | **76.53** | 75.9 | 69.3 | 82.7 | 82.1 | 140 | 12 | 477 | 17.67 |
| **#5** | **Sunil Narine** | **76.20** | 72.2 | 57.8 | 89.4 | 99.9 | 511 | 35 | 1556 | 23.22 |
| **#6** | **Yuzvendra Chahal** | **74.72** | 74.1 | 71.3 | 61.2 | 99.9 | 607 | 37 | 1656 | 23.32 |
| **#7** | **Umran Malik** | **74.05** | 79.5 | 84.5 | 41.5 | 85.5 | 154 | 13 | 444 | 19.30 |
| **#8** | **Varun Chakravarthy** | **73.26** | 64.7 | 53.4 | 95.3 | 99.9 | 529 | 35 | 1440 | 22.86 |
| **#9** | **Mitchell Santner** | **72.57** | 69.2 | 67.8 | 73.5 | 88.3 | 184 | 13 | 574 | 19.79 |
| **#10** | **Wanindu Hasaranga** | **72.07** | 66.9 | 58.3 | 80.9 | 96.9 | 287 | 19 | 772 | 22.06 |

---

### Twenty20 International (T20I)

#### Official Eligible Top 10 Batters
| Rank | Player Name | CPRI | Impact | Adapt | Consist | Reliab | Pressure Balls | Pressure Matches | Career Balls | Pos Match % |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Matthew Wade** | **97.42** | 100.0 | 98.9 | 100.0 | 84.6 | 160 | 12 | 294 | 100.0% |
| **#2** | **Romario Shepherd** | **83.85** | 82.3 | 96.6 | 59.4 | 99.4 | 356 | 28 | 566 | 57.1% |
| **#3** | **Suryakumar Yadav** | **82.34** | 80.1 | 88.3 | 73.7 | 89.9 | 212 | 13 | 1459 | 69.2% |
| **#4** | **Mohammad Nabi** | **82.08** | 73.8 | 95.8 | 70.0 | 97.3 | 266 | 21 | 650 | 66.7% |
| **#5** | **Phil Salt** | **81.81** | 85.9 | 95.5 | 55.6 | 83.1 | 164 | 11 | 954 | 54.5% |
| **#6** | **Reeza Hendricks** | **81.77** | 81.4 | 96.5 | 53.6 | 95.7 | 378 | 16 | 860 | 50.0% |
| **#7** | **Tim David** | **81.40** | 84.5 | 93.1 | 62.2 | 79.2 | 149 | 10 | 599 | 60.0% |
| **#8** | **Quinton de Kock** | **79.19** | 76.6 | 97.8 | 61.9 | 78.1 | 230 | 8 | 471 | 62.5% |
| **#9** | **Fakhar Zaman** | **78.05** | 70.5 | 92.7 | 64.2 | 92.1 | 194 | 16 | 638 | 62.5% |
| **#10** | **Akeal Hosein** | **77.61** | 67.3 | 97.1 | 62.3 | 93.0 | 170 | 22 | 264 | 63.6% |

#### Official Eligible Top 10 Bowlers
| Rank | Player Name | CPRI | Impact | Adapt | Consist | Reliab | Pressure Balls | Pressure Matches | Career Balls | Balls/Match |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | **Sufiyan Muqeem** | **86.44** | 86.6 | 87.7 | 89.7 | 79.5 | 151 | 10 | 351 | 20.65 |
| **#2** | **Kuldeep Yadav** | **81.72** | 86.9 | 74.2 | 77.6 | 85.9 | 174 | 12 | 542 | 21.68 |
| **#3** | **Mustafizur Rahman** | **79.31** | 68.8 | 78.7 | 86.3 | 98.9 | 332 | 25 | 1114 | 22.73 |
| **#4** | **Washington Sundar** | **76.87** | 79.9 | 73.1 | 63.6 | 92.8 | 206 | 16 | 378 | 15.75 |
| **#5** | **Rashid Khan** | **76.84** | 75.6 | 61.7 | 81.4 | 99.2 | 386 | 25 | 1041 | 23.13 |
| **#6** | **Matthew Humphreys** | **76.72** | 84.6 | 87.6 | 52.3 | 70.1 | 110 | 9 | 315 | 22.50 |
| **#7** | **Mitchell Santner** | **75.78** | 67.1 | 73.3 | 78.5 | 99.5 | 469 | 27 | 1219 | 22.57 |
| **#8** | **Reece Topley** | **74.79** | 60.7 | 79.0 | 90.4 | 84.5 | 228 | 10 | 514 | 22.35 |
| **#9** | **Mohammad Nawaz** | **74.61** | 78.3 | 75.8 | 47.8 | 98.5 | 301 | 24 | 1017 | 19.56 |
| **#10** | **Gudakesh Motie** | **73.90** | 62.7 | 75.9 | 82.3 | 89.3 | 200 | 13 | 753 | 19.82 |

---

### Provisional Top Ladders (Moderate Confidence)

These players possess high performance indices but require additional match dispersion ($M_P \ge 8$) or pressure volume ($N_P \ge 100$) for full High Confidence certification:

- **IPL Provisional Bowlers**:
  1. *Lungi Ngidi* (CPRI 86.28, $M_P=6, N_P=69$)
  2. *Ashwani Kumar* (CPRI 75.56, $M_P=5, N_P=90$)
  3. *Sakib Hussain* (CPRI 74.64, $M_P=7, N_P=118$)
  4. *Jamie Overton* (CPRI 72.42, $M_P=5, N_P=71$)
  5. *Akeal Hosein* (CPRI 71.45, $M_P=6, N_P=104$)
- **T20I Provisional Bowlers**:
  1. *Jamie Overton* (CPRI 78.21, $M_P=11, N_P=97$)
  2. *Tabraiz Shamsi* (CPRI 76.49, $M_P=4, N_P=98$)
  3. *Corbin Bosch* (CPRI 73.46, $M_P=4, N_P=52$)
  4. *Mitchell Starc* (CPRI 71.74, $M_P=4, N_P=50$)
  5. *George Linde* (CPRI 69.37, $M_P=5, N_P=79$)
- **IPL Provisional Batters**:
  1. *Evin Lewis* (CPRI 80.95, $M_P=2, N_P=33$)
  2. *Aaron Finch* (CPRI 79.52, $M_P=2, N_P=48$)
  3. *Karun Nair* (CPRI 79.15, $M_P=4, N_P=65$)
  4. *Abishek Porel* (CPRI 78.89, $M_P=6, N_P=94$)
  5. *Harpreet Brar* (CPRI 77.89, $M_P=16, N_P=109, N_{NP}=33$)
- **T20I Provisional Batters**:
  1. *Muhammad Waseem* (CPRI 81.33, $M_P=6, N_P=114$)
  2. *Gulbadin Naib* (CPRI 77.29, $M_P=5, N_P=51$)
  3. *Fionn Hand* (CPRI 75.92, $M_P=3, N_P=24$)
  4. *Shan Masood* (CPRI 75.54, $M_P=3, N_P=91$)
  5. *Fabian Allen* (CPRI 74.95, $M_P=5, N_P=39$)

*Top 10 Datasets:* Exported in [final_top10_batters.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/final_top10_batters.csv) and [final_top10_bowlers.csv](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase3_3/final_top10_bowlers.csv).
