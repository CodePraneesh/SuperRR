# SupeRR Intelligence — CPRI High-Volume Pressure Performance Ranking Upgrade

**Document Version**: v4.0.0  
**Status**: Exploratory, post-hoc — committed together with the code it analyses; not pre-registered  
**Date**: November 15, 2026  
**Author**: SupeRR Intelligence Analytics & Release Engineering Team  

---

## 1. Executive Summary & Objective

In the initial Phase 8 submission, the Composite Pressure Resilience Index (CPRI) successfully established four grounded components:
- **Pressure Impact (PI, 40%)**: Delivery-level run and survival residuals relative to context-aware baseline expectations.
- **Pressure Adaptability (PA, 25%)**: Performance differential between high-pressure and standard deliveries.
- **Clutch Consistency (CC, 20%)**: Match-to-match stability and positive match impact ratio.
- **Reliability Confidence (RC, 15%)**: Non-linear volume and match dispersion saturation.

While rigorous, ranking players solely by raw CPRI allowed low-volume rate outliers to occupy top leaderboard spots (e.g. Matthew Wade at 191 pressure balls, Sufiyan Muqeem at 151 pressure balls) despite having limited exposure compared to multi-season clutch pillars (e.g. Suryakumar Yadav at 749 pressure balls, Rashid Khan at 970 pressure balls).

The **High-Volume Pressure Performance Ranking Upgrade** addresses this by:
1. **Preserving Raw CPRI**: Original frozen Phase 8 scores and rankings remain completely unmodified for transparency and competition compliance.
2. **Classifying Evidence Tiers**: Establishing statistically grounded, configurable sample-size tiers based on pressure deliveries.
3. **Introducing Pressure Performance Reliability (PPR)**: A new metric capturing role-specific delivery success, cross-match consistency, and Bayesian exposure credibility.
4. **Volume-Adjusted CPRI (Adjusted CPRI)**: Proportionately regressing small samples toward the population mean (note: sample size enters three times — see Section 7 Limitations), ensuring high-volume proven clutch match-winners are recognized while preventing volume from compensating for poor play.
5. **Main Leaderboard Eligibility**: Requiring at least 400 pressure balls ($\ge$ Strong Evidence) for the headline Main Leaderboard, while partitioning emerging talents into a separate, transparent Contenders section.

---

## 2. Configurable Evidence Tier Classification

Players are categorized into sample-size evidence tiers based on qualifying pressure deliveries ($N$, where delivery pressure index $\text{PI} \ge 50.0$):

| Evidence Tier | Pressure Deliveries ($N$) | Eligibility Category | Rationale & Statistical Credibility |
| :--- | :--- | :--- | :--- |
| **Elite Evidence** | **600+ balls** | Main Leaderboard | Extensive multi-year sample; standard error $\sigma_N \le 0.04$; high statistical power. |
| **Strong Evidence** | **400–599 balls** | Main Leaderboard | Robust tournament sample across dozens of matches; reliable clutch signal. |
| **Moderate Evidence** | **250–399 balls** | Contender / Emerging | Meaningful sample, but subject to moderate variance; eligible for emerging recognition. |
| **Limited Evidence** | **150–249 balls** | Contender / Emerging | Minimum threshold for initial evaluation; rates require significant shrinkage. |
| **Insufficient Evidence** | **Below 150 balls** | Excluded from Ranking | Extreme small-sample noise; excluded from ranked recommendations. |

```python
@dataclass
class EvidenceTierConfig:
    elite_threshold: int = 600
    strong_threshold: int = 400
    moderate_threshold: int = 250
    limited_threshold: int = 150
```

---

## 3. Role-Specific Pressure Success Measurement

Unlike naive counting statistics, success under pressure is evaluated at the granular delivery level against expected outcomes:

### 3.1 Batters
A delivery under pressure is classified as **Successful** ($S_i = 1$) if:
$$\text{Success}_i = (\text{actual\_batter\_runs}_i \ge 4) \lor (\text{batting\_run\_residual}_i > 0)$$
Where:
- $\text{batting\_run\_residual}_i = \text{actual\_batter\_runs}_i - \text{expected\_batter\_runs}_i$
- Boundaries (4s and 6s) generate immediate high-leverage value.
- Non-boundary deliveries that produce runs above expectation (e.g., tight singles or twos when expected runs were 0.70) reflect successful strike rotation.
- **Dismissal Frequency**: $\frac{\text{outs}}{N} \times 100$ measures wicket preservation under pressure.

### 3.2 Bowlers
A delivery under pressure is classified as **Successful** ($S_i = 1$) if:
$$\text{Success}_i = (\text{actual\_runs\_conceded}_i == 0) \lor (\text{actual\_wicket}_i == 1) \lor (\text{bowling\_run\_residual}_i < 0)$$
Where:
- $\text{bowling\_run\_residual}_i = \text{actual\_runs\_conceded}_i - \text{expected\_runs\_conceded}_i$
- Dot balls ($\text{runs} = 0$) create scoreboard pressure.
- Wickets directly terminate batting resources.
- Run suppression below expectations reflects execution quality.

---

## 4. Pressure Performance Reliability (PPR) Formulation

The **PPR Score** $[0, 100]$ combines four independent pillars:
1. **Performance vs. Expectations**: Pressure Impact Score ($PI$).
2. **Tactical Adaptability**: Pressure Adaptability Score ($PA$).
3. **Cross-Match Consistency**: Clutch Consistency Score ($CC$).
4. **Role-Specific Success Rate**: Normalized success rate ($S_{\text{norm}}$).

### Mathematical Definition
First, role-appropriate success rates are normalized to $[0, 100]$:
$$S_{\text{norm}} = 50.0 + \left( \frac{\text{SuccessRate}_{\%} - \mu_{\text{role}}}{\sigma_{\text{role}}} \right) \times 15.0$$
*(For Batters: $\mu = 30.0\%, \sigma = 6.0\%$; For Bowlers: $\mu = 60.0\%, \sigma = 8.0\%$)*

The **Clutch Quality Index (CQI)** isolates pure performance quality independent of sample size:
$$\text{CQI} = 0.35 \times PI + 0.25 \times PA + 0.20 \times CC + 0.20 \times S_{\text{norm}}$$

Sample-size credibility follows an empirical Bayes prior with equivalent sample size $N_{\text{prior}} = 250$:
$$\lambda(N) = \frac{N}{N + 250.0}$$
$$\text{PPR} = 50.0 + (\text{CQI} - 50.0) \times \lambda(N)$$

### Key Properties:
- **Baseline Invariance**: A player with zero sample defaults to neutral $50.0$.
- **Small-Sample Dampening**: A player with extreme rate performance ($CQI = 90.0$) but only 191 balls receives $\lambda(191) = 0.433$, shrinking their PPR to $67.3$.
- **No Reward for Poor Play**: If a player has below-average performance ($CQI < 50.0$), $(\text{CQI} - 50.0)$ is negative. Larger exposure drives their score closer to their low performance, never elevating them above high-performing players.

---

## 5. Volume-Adjusted CPRI Formulation

Adjusted CPRI separates raw skill from exposure. **Important accuracy note**: sample size is NOT avoided from double-counting — it enters three times: (1) skill shrinkage κ(N) = N/(N+150) in Step 2 below; (2) PPR credibility λ(N) = N/(N+250) in Section 4; and (3) the Reliability Confidence (RC) term already incorporates non-linear ball saturation. Additionally, PPR reuses the PI/PA/CC components from the original CPRI formula, introducing further correlation.

1. **Unweighted Raw Skill**:
   $$\text{Skill}_{\text{raw}} = \frac{0.40 \times PI + 0.25 \times PA + 0.20 \times CC}{0.85}$$
2. **Empirical Bayes Shrinkage**:
   $$\kappa(N) = \frac{N}{N + 150.0}$$
   $$\text{Skill}_{\text{shrunk}} = 50.0 + (\text{Skill}_{\text{raw}} - 50.0) \times \kappa(N)$$
3. **Composite Adjusted CPRI**:
   $$\text{CPRI}_{\text{adj}} = 0.60 \times \text{Skill}_{\text{shrunk}} + 0.20 \times RC + 0.20 \times \text{PPR}$$

---

## 6. Diagnostic Results & Verification

### 6.1 Batters Comparison Table

| Player Name | Pressure Deliveries | Evidence Tier | Raw CPRI (Phase 8 Rank) | Adjusted CPRI | PPR Score | Success Rate % | Eligibility Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Suryakumar Yadav** | 749 | **Elite Evidence** | 81.42 (#3) | **77.18 (#1 Main)** | 67.79 | 31.24% | **Main Leaderboard** |
| **Tim David** | 476 | **Strong Evidence** | 82.44 (#2) | **75.41 (#2 Main)** | 66.88 | 31.72% | **Main Leaderboard** |
| **Namboori Tilak Varma**| 777 | **Elite Evidence** | 74.81 (#8) | **72.13 (#3 Main)** | 61.37 | 26.64% | **Main Leaderboard** |
| **Rinku Singh** | 457 | **Strong Evidence** | 77.18 (#5) | **71.23 (#4 Main)** | 62.21 | 27.13% | **Main Leaderboard** |
| **Romario Shepherd** | 428 | **Strong Evidence** | 75.33 (#7) | **69.84 (#5 Main)** | 60.90 | 27.34% | **Main Leaderboard** |
| **Ravindra Jadeja** | 467 | **Strong Evidence** | 73.70 (#10) | **69.15 (#6 Main)** | 59.87 | 26.12% | **Main Leaderboard** |
| **Tristan Stubbs** | 579 | **Strong Evidence** | 69.55 (#14) | **67.47 (#7 Main)** | 57.77 | 27.81% | **Main Leaderboard** |
| **Nicholas Pooran** | 673 | **Elite Evidence** | 68.43 (#19) | **67.23 (#8 Main)** | 57.16 | 27.93% | **Main Leaderboard** |
| **David Miller** | 664 | **Elite Evidence** | 67.60 (#21) | **66.50 (#9 Main)** | 56.13 | 27.11% | **Main Leaderboard** |
| **Ayush Badoni** | 416 | **Strong Evidence** | 69.60 (#13) | **65.97 (#10 Main)**| 58.77 | 30.05% | **Main Leaderboard** |
| *Reeza Hendricks* | 378 | *Moderate Evidence* | 77.45 (#4) | *69.38 (#1 Contender)* | 63.37 | 29.37% | Contender / Emerging |
| *Matthew Wade* | 191 | *Limited Evidence* | 85.36 (#1) | *67.39 (#2 Contender)* | 65.65 | 36.13% | Contender / Emerging |
| *Phil Salt* | 261 | *Moderate Evidence* | 76.96 (#6) | *66.91 (#3 Contender)* | 63.73 | 37.55% | Contender / Emerging |
| *Dinesh Karthik* | 277 | *Moderate Evidence* | 74.54 (#9) | *65.90 (#5 Contender)* | 60.69 | 29.96% | Contender / Emerging |

### 6.2 Bowlers Comparison Table

| Player Name | Pressure Deliveries | Evidence Tier | Raw CPRI (Phase 8 Rank) | Adjusted CPRI | PPR Score | Success Rate % | Eligibility Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rashid Khan** | 970 | **Elite Evidence** | 77.90 (#3) | **75.49 (#1 Main)** | 65.61 | 60.93% | **Main Leaderboard** |
| **Mitchell Santner** | 653 | **Elite Evidence** | 79.84 (#1) | **75.27 (#2 Main)** | 65.39 | 58.50% | **Main Leaderboard** |
| **Varun Chakravarthy**| 892 | **Elite Evidence** | 73.02 (#9) | **71.81 (#3 Main)** | 63.01 | 65.02% | **Main Leaderboard** |
| **Matheesha Pathirana**| 557 | **Strong Evidence** | 75.77 (#5) | **71.44 (#4 Main)** | 62.50 | 58.35% | **Main Leaderboard** |
| **Sunil Narine** | 511 | **Strong Evidence** | 75.63 (#6) | **71.10 (#5 Main)** | 62.13 | 58.71% | **Main Leaderboard** |
| **Yuzvendra Chahal** | 859 | **Elite Evidence** | 73.01 (#10) | **70.98 (#6 Main)** | 59.41 | 53.20% | **Main Leaderboard** |
| **Jasprit Bumrah** | 606 | **Elite Evidence** | 73.36 (#8) | **70.84 (#7 Main)** | 62.83 | 66.34% | **Main Leaderboard** |
| **Wanindu Hasaranga** | 639 | **Elite Evidence** | 71.86 (#13) | **69.81 (#8 Main)** | 61.24 | 63.69% | **Main Leaderboard** |
| **Mustafizur Rahman** | 527 | **Strong Evidence** | 72.12 (#12) | **69.52 (#9 Main)** | 62.54 | 69.26% | **Main Leaderboard** |
| **Kuldeep Yadav** | 627 | **Elite Evidence** | 71.29 (#14) | **68.95 (#10 Main)**| 58.65 | 56.46% | **Main Leaderboard** |
| *Mohammad Nawaz* | 301 | *Moderate Evidence* | 75.51 (#7) | *67.51 (#1 Contender)* | 62.99 | 68.77% | Contender / Emerging |
| *Jamie Overton* | 168 | *Limited Evidence* | 76.92 (#4) | *61.92 (#9 Contender)* | 60.29 | 61.90% | Contender / Emerging |
| *Sufiyan Muqeem* | 151 | *Limited Evidence* | 78.78 (#2) | *60.94 (#11 Contender)*| 61.21 | 72.19% | Contender / Emerging |

### 6.3 Diagnostic Check: High-Volume Low-Performers
Confirming that volume alone does NOT artificially inflate ranking:
- **Mukesh Kumar** (445 balls): Runs saved = -131.08, Impact = 21.13 $\implies$ Adjusted CPRI = 42.21, PPR = 36.36.
- **Axar Patel** (614 balls): Run residual = +6.39, Impact = 43.29 $\implies$ Adjusted CPRI = 55.48, PPR = 46.84.
- **Rohit Sharma** (447 balls): Run residual = +3.07, Impact = 44.33 $\implies$ Adjusted CPRI = 54.90, PPR = 48.46.

None of these high-exposure players rise to the top ranks because their underlying clutch efficiency is substandard.



---

## 7. Limitations

**This document describes an exploratory, post-hoc analysis. It was committed in the same commit as the code it describes (49d059) and was motivated by observations about named players. It is NOT pre-registered.**

The following constants and design choices in this upgrade are hand-chosen and lack held-out empirical validation:

- **400-ball main leaderboard cutoff**: Chosen based on domain intuition, not cross-validated against an external outcome measure.
- **Bayesian priors**: The skill shrinkage prior of N₀ = 150 (κ = N/(N+150)) and the PPR credibility prior of N₀ = 250 (λ = N/(N+250)) are set by convention; no grid search or leave-one-out validation was performed.
- **PPR component weights**: The weights 0.60 (Skill_shrunk), 0.20 (RC), 0.20 (PPR) in the Adjusted CPRI formula, and the 0.35/0.25/0.20/0.20 CQI sub-weights, are hand-chosen. Alternative weightings were not formally evaluated.
- **Role-specific success norms**: The batter success-rate norm (μ = 30%, σ = 6%) and bowler norm (μ = 60%, σ = 8%) are set by convention, not empirically derived from the population distribution.
- **No held-out validation was run**: The upgrade was not tested on a held-out set of matches or a future season. The in-sample diagnostic tables (Section 6) cannot substitute for out-of-sample validation.
- **Phase 8 outperformed shrinkage-based methods on split-half reliability**: In the v2 evaluation (pre-registered in docs/methodology/v2/PREREGISTRATION.md), the Phase 8 baseline achieved higher split-half reliability (batter ρ = 0.440, bowler ρ = 0.195) compared to Empirical Bayes shrinkage variants. The adjusted CPRI has not been shown to improve on this.
- **Triple sample-size use**: As noted in Section 5, sample size N enters the Adjusted CPRI three times (κ, λ, and RC), and PPR reuses PI/PA/CC components. This compounding is not corrected for and may cause the adjusted scores to overweight high-volume players more than any single Bayesian shrinkage approach would.

**The official lists are Phase 13 (≥ 250 pressure balls, post-hoc) and Phase 8 is the supplementary pre-floor baseline. The Adjusted CPRI / PPR view is strictly an exploratory post-hoc analysis.**
