# Statistical Audit: Contradiction Investigation for Matthew Wade

**Author:** SupeRR Intelligence Analytical & Release Engineering Team  
**Date:** 16 November 2026  
**Status:** Authoritative Repository Audit  
**Scope:** Raw match data, frozen Phase 8 baseline, codebase thresholds, and external claim verification  

---

## 1. Executive Summary & Comparison Table

An external text asserted that **Matthew Wade** has:
> *"109 pressure deliveries across 8 matches, a pressure strike rate of 159.63 vs a normal strike rate of 131.45, and was excluded by a rule of 'at least 50 pressure deliveries across at least 10 distinct matches'."*

An exhaustive audit of the SupeRR Intelligence repository, git commit history, and raw ball-by-ball match dataset proves that **this claim does not describe our pipeline**. 

In the official, frozen **SupeRR Intelligence Phase 8 pipeline**, Matthew Wade has:
* **191 pressure deliveries** (not 109)
* **15 distinct pressure matches** (not 8)
* **165.97 pressure strike rate** (not 159.63)
* **107.84 non-pressure strike rate** and **132.74 overall strike rate** (not 131.45)
* Meets all eligibility criteria and is classified as **"Official Eligible"** (Rank #1, CPRI 85.36).

Furthermore, the rule *"at least 50 pressure deliveries across at least 10 distinct matches"* **does not exist anywhere in our code or commit history**. The term *"RoyalEdge"* has **zero hits** in the repository.

### Comparison Summary

| Metric / Attribute | Claimed External Figure | SupeRR Intelligence Pipeline (Phase 8 Frozen) | Status / Concordance |
| :--- | :---: | :---: | :--- |
| **Total Deliveries Faced** | *Unstated* | **446** | Recomputed from raw ball-by-ball data |
| **Total Matches Batted** | *Unstated* | **30** | 10 IPL + 20 T20I matches |
| **Pressure Deliveries ($N_P$)** | 109 | **191** | Exact match in `batter_full_population.csv` |
| **Pressure Matches ($M_P$)** | 8 | **15** | Exact match in `batter_full_population.csv` |
| **Pressure Runs Scored** | *Unstated* | **317** | Recomputed from raw ball-by-ball data |
| **Pressure Strike Rate** | 159.63 | **165.97** | $317 / 191 \times 100 = 165.9685\dots$ |
| **Non-Pressure Strike Rate** | 131.45 ("normal SR") | **107.84** | $275 / 255 \times 100 = 107.8431\dots$ |
| **Overall Career Strike Rate** | *Unstated* | **132.74** | $592 / 446 \times 100 = 132.7354\dots$ |
| **Eligibility Rule Applied** | $\ge 50$ balls, $\ge 10$ matches | **$\ge 100$ balls, $\ge 8$ matches, $\ge 30$ non-pressure** | Documented in `scripts/execute_phase8_analysis.py` |
| **Eligibility Classification** | "Excluded" | **"Official Eligible" (Rank #1, CPRI 85.36)** | Authoritative submission deliverable |
| **Term "RoyalEdge"** | Used in external text | **0 occurrences across repository** | Third-party project artifact |

---

## 2. Codebase & Git History Audit: Eligibility Rules & Tiers

We searched the entire repository across tracked files, untracked artifacts, and full git history (`git log -S`) for eligibility logic and tier generation.

### Exact Thresholds Used in Code
The authoritative classification logic resides in [`scripts/execute_phase8_analysis.py`](file:///c:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/scripts/execute_phase8_analysis.py#L267-L290):

#### Batters (Lines 267–290)
```python
# Assign eligibility tiers
is_off_eligible_bat = (
    (bat_pop['pressure_deliveries'] >= 100) & 
    (bat_pop['pressure_matches'] >= 8) & 
    (bat_pop['nonpressure_deliveries'] >= 30)
)
is_prov_bat = (
    ~is_off_eligible_bat & 
    (bat_pop['pressure_deliveries'] >= 40) & 
    (bat_pop['pressure_matches'] >= 3)
)

bat_pop['eligibility_tier'] = np.where(
    is_off_eligible_bat, 'Official Eligible',
    np.where(is_prov_bat, 'Provisional Tier', 'Ineligible')
)
```

#### Bowlers (Lines 423–450)
```python
# Assign eligibility tiers
is_off_eligible_bowl = (
    (bowl_pop['pressure_deliveries'] >= 80) & 
    (bowl_pop['pressure_matches'] >= 8) & 
    (bowl_pop['nonpressure_deliveries'] >= 30) &
    (bowl_pop['total_deliveries'] >= 180) # at least 30 total overs bowled across career
)
is_prov_bowl = (
    ~is_off_eligible_bowl & 
    (bowl_pop['pressure_deliveries'] >= 40) & 
    (bowl_pop['pressure_matches'] >= 3)
)

bowl_pop['eligibility_tier'] = np.where(
    is_off_eligible_bowl, 'Official Eligible',
    np.where(is_prov_bowl, 'Provisional Tier', 'Ineligible')
)
```

### Key Findings on Eligibility Rules
1. **Batter Threshold**: Requires $N_P \ge 100$ pressure deliveries and $M_P \ge 8$ pressure matches, plus $N_{NP} \ge 30$ baseline deliveries. 
2. **Bowler Threshold**: Requires $N_P \ge 80$ pressure deliveries, $M_P \ge 8$ pressure matches, $N_{NP} \ge 30$, and $N_{\text{total}} \ge 180$ career balls (30 overs).
3. **No 50-ball / 10-match Rule**: The rule *"$\ge 50$ pressure deliveries across $\ge 10$ distinct matches"* does not appear anywhere in SupeRR Intelligence.

---

## 3. Search for Specific Claimed Terms

We executed git grep across the repository for each specific token:

```bash
git grep -i "RoyalEdge"
git grep "159.63"
git grep "131.45"
git grep "109"
```

### Results
1. **"RoyalEdge"**: **0 hits**. This term is completely absent from all source code, documentation, reports, JSON stores, and git commit messages. It appears to be the moniker of an external competitor team or third-party script.
2. **"159.63"**: **1 hit**, located in `output/phase10_ranking_validation/phase10_innings_phase_robustness.csv` (Row 4, Reeza Hendricks, middle-overs strike rate = 159.63). It is never associated with Matthew Wade.
3. **"131.45"**: **1 hit**, located in `output/phase8_ranking_reconsideration/batter_full_population.csv` (Row 482, Prasidh Krishna, consistency score = 131.45). It is never associated with Matthew Wade.
4. **"109"**: Matthew Wade has 105 deliveries in low pressure ($PI < 25$), but nowhere in the repository or data is Wade linked to 109 pressure deliveries.

---

## 4. Recomputation of Matthew Wade from Raw Match Data

Using the pure Phase 8 pre-delivery pressure formulation (Dynamic Pressure Engine with $PI \ge 50.0$) evaluated strictly on in-scope competitions (IPL and senior men's T20Is):

### Python Verification Command
```python
import zipfile, pandas as pd
from ml.phase2.pressure_engine import DynamicPressureEngine

# Load raw ball-by-ball and match metadata
zip_path = "SupeRR_Intelligence_Phase1.zip"
with zipfile.ZipFile(zip_path, 'r') as z:
    with z.open('SupeRR_Phase1/output/processed/matches_enriched.csv') as fm:
        m_df = pd.read_csv(fm)
    with z.open('SupeRR_Phase1/output/processed/deliveries_enriched.csv') as fd:
        df = pd.read_csv(fd)

# Add scope & compute dynamic pressure
m_df['competition_scope'] = [
    'IPL' if str(r['comp_name']).startswith('IPL')
    else ('T20I' if str(r['match_format']) == 'T20I' else 'Other')
    for _, r in m_df.iterrows()
]
df = df.merge(m_df[['match_id', 'competition_scope']], on='match_id', how='left')

engine = DynamicPressureEngine()
scored = engine.score_deliveries(df, excluded_matches=set())
wade = scored[(scored['striker_id'] == 796) & (scored['in_scope_competition'] == True)]
p_wade = wade[wade['pressure_score'] >= 50.0]
```

### Recomputed Figures
* **Total Deliveries Faced**: **446**
* **Total Matches**: **30**
* **Total Runs Scored**: **592**
* **Overall Strike Rate**: **132.74** ($592 / 446 \times 100$)
* **Pressure Deliveries ($PI \ge 50.0$)**: **191**
* **Pressure Runs**: **317**
* **Pressure Strike Rate**: **165.97** ($317 / 191 \times 100$)
* **Non-Pressure Deliveries ($PI < 50.0$)**: **255**
* **Non-Pressure Runs**: **275**
* **Non-Pressure Strike Rate**: **107.84** ($275 / 255 \times 100$)
* **Pressure Matches**: **15 distinct matches**

### The 15 Pressure Matches for Matthew Wade
The 15 in-scope matches where Matthew Wade faced deliveries with pre-ball pressure index $PI \ge 50.0$:

| # | Match ID | Match Date | Tournament / Competition | Innings | Pressure Balls Faced | Pressure Runs Scored |
| :-: | :---: | :---: | :--- | :-: | :-: | :-: |
| 1 | `13613` | 2022-02-13 | Sri Lanka in Australia T20I Series 2022 | 1 | 3 | 12 |
| 2 | `13616` | 2022-02-20 | Sri Lanka in Australia T20I Series 2022 | 1 | 21 | 33 |
| 3 | `14109` | 2022-04-08 | IPL 2022 | 2 | 2 | 1 |
| 4 | `15187` | 2022-05-24 | IPL 2022 | 2 | 22 | 31 |
| 5 | `17394` | 2022-09-20 | Australia in India T20I Series 2022 | 2 | 19 | 36 |
| 6 | `17395` | 2022-09-23 | Australia in India T20I Series 2022 | 1 | 13 | 36 |
| 7 | `17640` | 2022-10-05 | West Indies in Australia T20I Series 2022 | 2 | 1 | 4 |
| 8 | `17763` | 2022-10-09 | England in Australia T20I Series 2022 | 2 | 14 | 21 |
| 9 | `17764` | 2022-10-12 | England in Australia T20I Series 2022 | 2 | 11 | 10 |
| 10 | `27061` | 2023-11-26 | Australia in India T20I Series 2023 | 2 | 23 | 42 |
| 11 | `27062` | 2023-11-28 | Australia in India T20I Series 2023 | 2 | 16 | 28 |
| 12 | `27063` | 2023-12-01 | Australia in India T20I Series 2023 | 2 | 24 | 36 |
| 13 | `27064` | 2023-12-03 | Australia in India T20I Series 2023 | 2 | 8 | 16 |
| 14 | `29817` | 2024-02-13 | West Indies in Australia T20I Series 2024 | 2 | 7 | 7 |
| 15 | `31242` | 2024-04-10 | IPL 2024 | 2 | 7 | 4 |

These match counts, delivery totals, and run totals match [`output/phase8_ranking_reconsideration/batter_full_population.csv`](file:///c:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/output/phase8_ranking_reconsideration/batter_full_population.csv) exactly.

---

## 5. Variant Testing: Can the Claimed Numbers Be Reproduced?

We executed an automated sweep across:
* 65 pressure score thresholds ($PI \in [20, 85]$)
* 71 raw provisional pressure index thresholds ($\text{raw\_PI} \in [0.20, 0.90]$)
* Slices: All matches, In-Scope only, T20I only, IPL only, Chases only (Innings 2), 1st Innings only.

### Outcome
* **Zero slices** produced 109 pressure deliveries.
* **Zero slices** produced 8 matches with 109 balls.
* **Zero slices** produced 159.63 strike rate across 109 balls.
* In T20I cricket at $PI \ge 32$, Wade has 223 balls at a strike rate of 159.64, but this corresponds to 18 matches, not 8.

**Conclusion**: The figures in the prompt belong to an entirely different model, dataset, or competitor submission (likely titled *"RoyalEdge"*), and bear no relationship to the SupeRR Intelligence pipeline.

---

## 6. Hypothetical Sensitivity Analysis: Minimum Match Thresholds

As an exploratory analysis, we evaluated the sensitivity of the frozen Official Phase 8 Top 10 to hypothetical minimum pressure match thresholds ($M_P \ge 8$, $M_P \ge 10$, and $M_P \ge 12$), while keeping all other eligibility filters ($N_P \ge 100$ for batters, $N_P \ge 80$ for bowlers) fixed.

> **Note**: This sensitivity analysis is strictly **hypothetical and post-hoc**. It does not modify the frozen Phase 8 submission deliverables.

### Batter Population Distribution (Official Top 10)
| Official Rank | Player Name | Pressure Matches ($M_P$) | Pressure Balls ($N_P$) | CPRI Score |
| :-: | :--- | :-: | :-: | :---: |
| #1 | Matthew Wade | 15 | 191 | 85.36 |
| #2 | Tim David | 37 | 476 | 82.44 |
| #3 | Suryakumar Yadav | 41 | 749 | 81.42 |
| #4 | Reeza Hendricks | 16 | 378 | 77.45 |
| #5 | Rinku Singh | 30 | 457 | 77.18 |
| #6 | Phil Salt | 20 | 261 | 76.96 |
| #7 | Romario Shepherd | 38 | 428 | 75.33 |
| #8 | Namboori Tilak Varma | 43 | 777 | 74.81 |
| #9 | Dinesh Karthik | 23 | 277 | 74.54 |
| #10 | Ravindra Jadeja | 34 | 467 | 73.70 |

*Every single batter in the Official Top 10 has at least 15 pressure matches.* Even under a strict hypothetical threshold of 10 or 12 matches, **zero batters drop out**. Matthew Wade remains Rank #1.

### Bowler Population Distribution (Official Top 10)
| Official Rank | Player Name | Pressure Matches ($M_P$) | Pressure Balls ($N_P$) | CPRI Score |
| :-: | :--- | :-: | :-: | :---: |
| #1 | Mitchell Santner | 40 | 653 | 79.84 |
| #2 | Sufiyan Muqeem | 10 | 151 | 78.78 |
| #3 | Rashid Khan | 65 | 970 | 77.90 |
| #4 | Jamie Overton | 16 | 168 | 76.92 |
| #5 | Matheesha Pathirana | 29 | 557 | 75.77 |
| #6 | Sunil Narine | 35 | 511 | 75.63 |
| #7 | Mohammad Nawaz | 24 | 301 | 75.51 |
| #8 | Jasprit Bumrah | 44 | 606 | 73.36 |
| #9 | Varun Chakravarthy | 57 | 892 | 73.02 |
| #10 | Yuzvendra Chahal | 53 | 859 | 73.01 |

### Top-10 Movement Under Hypothetical Rules

| Threshold | Batters Dropping Out | Batters Entering | Bowlers Dropping Out | Bowlers Entering |
| :--- | :--- | :--- | :--- | :--- |
| **$M_P \ge 8$** *(Current)* | **None** | **None** | **None** | **None** |
| **$M_P \ge 10$** *(Hypothetical)* | **None** | **None** | **None** | **None** |
| **$M_P \ge 12$** *(Hypothetical)* | **None** | **None** | **Sufiyan Muqeem** ($M=10$) | **Abrar Ahmed** (Rank #11, CPRI 72.93, $M=21$) |

Under $M_P \ge 12$, Sufiyan Muqeem ($M=10$) is the sole player in either Top 10 who would fail the match threshold. He would be replaced by Pakistan spinner **Abrar Ahmed** (CPRI: 72.93, 21 pressure matches, 291 pressure balls).

---

## 7. Audit Conclusion & Verdict

1. **Matthew Wade's Status in SupeRR Intelligence**:
   - Deliveries: **191** pressure deliveries (well above the 100-ball threshold).
   - Matches: **15** pressure matches (well above the 8-match threshold).
   - Strike Rates: **165.97** in pressure, **107.84** in non-pressure, **132.74** overall.
   - Classification: Fully **Official Eligible**; Rank #1 in frozen Phase 8 submission.
2. **Origin of the Contradiction**:
   - The claimed statistics (109 balls, 8 matches, 159.63 SR, 131.45 normal SR, "RoyalEdge", $\ge 50$ balls across $\ge 10$ matches) are from an external third-party analysis or competing project. They do not exist anywhere in this repository or dataset.
3. **Integrity Confirmation**:
   - All 17 deliverables in `output/phase8_ranking_reconsideration/` remain cryptographically verified and 100% untouched.
