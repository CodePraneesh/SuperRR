# SupeRR Intelligence v2: Methodology, Candidate Evaluations, & Final Selection

**Project**: SupeRR Intelligence (SupeRR Selector Season 2, Round 1)  
**Document Status**: Official v2 Research & Evaluation Report  
**Pre-Registration Reference**: [`docs/methodology/v2/PREREGISTRATION.md`](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/docs/methodology/v2/PREREGISTRATION.md)  
**Audit Findings Reference**: [`docs/methodology/v2/AUDIT_FINDINGS.md`](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/docs/methodology/v2/AUDIT_FINDINGS.md)  
**Pipeline Location**: `ml/phase11_v2/`  
**Output Deliverables**: `output/phase11_v2/`  

---

## 1. Problem Statement & Phase 8 Audit Findings

In Phase 8, the SupeRR Intelligence CPRI v1.0 methodology established a foundational pressure-performance ranking for IPL and T20 International cricket. However, an in-depth statistical audit revealed four structural limitations:

1. **Over-Rewarding of Small Samples**:
   - In Phase 8, Matthew Wade ranked #1 among batters with only 191 pressure deliveries (Rank CI [1, 22]), and Sufiyan Muqeem ranked #2 among bowlers with only 196 pressure deliveries (Rank CI [1, 74]). Point-estimate ranking without formal hierarchical shrinkage rewarded noisy, high-variance estimates.
2. **Double-Counting & Collinear Weights**:
   - CPRI defined:
     $$\text{CPRI} = 0.40 \times \text{Impact} + 0.25 \times \text{Adaptability} + 0.20 \times \text{Consistency} + 0.15 \times \text{Reliability}$$
   - Where $\text{Adaptability} = 0.60 \times \text{Impact} + 0.40 \times \text{ContextDelta}$.
   - Consequently, Pressure Impact entered with an effective weight of $0.40 + 0.25 \times 0.60 = 55\%$, reducing Context Delta to only $10\%$. Component weights and constants (e.g. wicket value 12.0, WPA multiplier 25.0) were hand-tuned rather than empirically grounded.
3. **League Comparability**:
   - Single-league players (IPL-only or T20I-only) were evaluated on the same baseline as dual-league players without explicitly modeling league-level fixed/random effects.
4. **Underestimated Uncertainty from Delivery-Level Resampling**:
   - Earlier bootstrap routines resampled individual deliveries. Because deliveries within a cricket match are correlated (shared pitch, match leverage, opposition, and weather), delivery-level resampling violated exchangeability and artificially narrowed confidence intervals.

The goal of the **v2 Pipeline** is to develop a mathematically principled, auditable alternative that addresses these weaknesses through pre-registered candidate models, match-level cluster bootstrapping, and strict out-of-sample validation.

---

## 2. Dataset Scope & Anti-Leakage Audit

### 2.1 Verified Match & Delivery Corpus
- **Raw Corpus**: 883 matches, 200,999 deliveries.
- **Emerging Teams Filter**: Exactly 30 Emerging Teams T20 matches (6,985 deliveries) were excluded from all baselines and evaluations.
- **In-Scope Dataset**: Exactly **853 matches** (371 IPL, 482 T20I) containing **194,014 deliveries**.
- **Temporal Span**: January 2022 to November 2026.
- **Zero Lookahead Audit**: All cumulative state variables (`score_before`, `wickets_lost_before`, `legal_balls_before`, `balls_remaining`, `runs_required`) are derived strictly via `shift(fill_value=0)`. On ball 1 of every innings, `score_before == 0`, `wickets_lost_before == 0`, and zero post-delivery information is accessible.

### 2.2 Pressure Definition & Sensitivity
Pressure is evaluated strictly prior to each delivery:
- **Benchmark ($\text{PI} \ge 50.0$)**: 61,719 in-scope deliveries (31.8% of deliveries).
- **Broad ($\text{PI} \ge 40.0$)**: 79,782 deliveries (41.1%).
- **High-Crisis ($\text{PI} \ge 60.0$)**: 44,363 deliveries (22.9%).

### 2.3 Eligibility Thresholds
- **Primary Eligibility**: Minimum **60 legal pressure deliveries** faced/bowled and minimum **5 distinct pressure matches**.
- **Qualified Pool**: Exactly 256 eligible Batters and 212 eligible Bowlers.

---

## 3. Candidate Methods Formulations

All candidate methods were declared in advance in [`PREREGISTRATION.md`](file:///C:/Users/Praneesh/OneDrive/Desktop/RR/SupeRR_Intelligence_Phase1/SupeRR_Phase1/docs/methodology/v2/PREREGISTRATION.md):

### Method A: Phase 8 Baseline Reproduction (Reference Anchor)
The frozen CPRI v1.0 formula with 40/25/20/15 component weights, sigmoid normalization, and sample saturation reliability.

### Method B: Hierarchical Empirical Bayes (EB)
Eliminates arbitrary weights by pooling delivery-level net value ($v_{i,d} = \text{RunResidual} + 12 \times \text{WicketResidual} + 25 \times \text{WPA}$) and shrinking each player's observed mean $\hat{\theta}_i$ toward the cohort prior $\mathcal{N}(\mu_0, \tau^2)$ via cluster-robust variance $s_i^2$:
$$B_i = \frac{s_i^2}{s_i^2 + \tau^2}, \quad \theta_i^{\text{EB}} = (1 - B_i) \hat{\theta}_i + B_i \mu_0$$
- **Variant B1 (Posterior Mean)**: Ranked by $\theta_i^{\text{EB}}$.
- **Variant B2 (20th Percentile LCB)**: Ranked by $\text{LCB}_{0.20} = \theta_i^{\text{EB}} - 0.8416 \times \sigma_{i,\text{post}}$. Penalizes high posterior uncertainty.

### Method C: Context- & Role-Adjusted Empirical Bayes
Conditions delivery expectations on competition scope, innings phase (Powerplay, Middle, Death), and innings leverage (1st vs 2nd innings) before applying Empirical Bayes shrinkage to the context-adjusted residuals.

### Method D: Non-Double-Counted Orthogonal Composite (v2 Pipeline)
Deconstructs performance into three strictly non-overlapping, orthogonal components:
1. $S_{\text{impact}}$: Shrunk net pressure value per delivery via Empirical Bayes ($\tau^2 = 0.015$).
2. $S_{\text{consistency}}$: Positive match contribution ratio shrunk toward cohort baseline ($\mu_0 = 0.50, M_0 = 10.0$):
   $$\text{pos\_ratio}_i^{\text{shrunk}} = \frac{M_{i,\text{pos}} + 10 \times 0.50}{M_i + 10}$$
   $$S_{\text{consistency}} = \text{clip}(\text{pos\_ratio}_i^{\text{shrunk}} \times 100.0, 0.0, 100.0)$$
3. $S_{\text{volume}}$: Formal sample information weight:
   $$w_{\text{vol},i} = \frac{M_i}{M_i + 10} \times \frac{N_i}{N_i + 100} \times 100$$
Composite score: $\text{Score} = 0.50 \times S_{\text{impact}} + 0.30 \times S_{\text{consistency}} + 0.20 \times S_{\text{volume}}$.

### Method E: Posterior Probability of True Top 10 (Bayesian Selection)
Simulates joint posterior skill draws across all eligible players:
$$P(\text{Top 10})_i = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(\text{Rank}_i^{(b)} \le 10)$$
Ranked primarily by $P(\text{Top 10})$, tie-broken by expected rank $\mathbb{E}[\text{Rank}_i]$.

---

## 4. Out-of-Sample Validation & Metric Results

In accordance with Section 7 of the pre-registration, all candidate methods were evaluated on held-out temporal data.
- **Train Period**: Earliest 70% matches (597 matches, Jan 2022 to mid-2025).
- **Test Period**: Latest 30% matches (256 matches, mid-2025 to late 2026).
- **Split-Half Reliability**: 25 independent 50/50 match cluster partitions.

### Comprehensive Evaluation Results Table (`candidate_methods_evaluation.csv`)

| Candidate Method | Batter Pred $\rho$ | Bowler Pred $\rho$ | Batter Hit Rate | Bowler Hit Rate | Batter Split-Half $\rho$ | Bowler Split-Half $\rho$ | Total CSI (Rank-Sum) | $\Delta\text{CSI}$ vs P8 | Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Method A (Phase 8 Baseline)** | **-0.0035** | **-0.0403** | 0.143 | 0.300 | **0.2887** | **0.3772** | **4.65** | **0.00** | **WINNER** |
| **Method D (Orthogonal Composite)** | -0.0431 | -0.0910 | 0.143 | 0.300 | 0.1898 | 0.2263 | **6.05** | +1.40 | 2nd Place |
| **Method B2 (EB 20th% LCB)** | -0.1307 | +0.0473 | 0.000 | 0.286 | 0.0446 | 0.0584 | **6.45** | +1.80 | 3rd Place |
| **Method B1 (EB Posterior Mean)** | -0.1509 | +0.0489 | 0.167 | 0.167 | 0.0173 | 0.0385 | **8.15** | +3.50 | 4th Place |
| **Method E (Bayesian P(Top 10))** | -0.1496 | +0.0255 | 0.333 | 0.167 | 0.0850 | 0.0139 | **8.15** | +3.50 | 5th Place |
| **Method C (Context-Adjusted EB LCB)**| -0.1418 | +0.0412 | 0.000 | 0.167 | 0.0302 | 0.0512 | **8.55** | +3.90 | 6th Place |

*Metric Definitions*:
- $\text{Pred } \rho$: Spearman rank correlation between fit-period rank and held-out performance rate.
- $\text{Hit Rate}$: Proportion of fit-period predicted Top 10 achieving top-quintile realized performance in test period.
- $\text{Split-Half } \rho$: Average rank stability across 50/50 match cluster splits.
- $\text{Total CSI}$: Weighted rank-sum across all 4 dimensions for Batters and Bowlers (lower is better).

---

## 5. Pre-Registered Decision & Scientific Conclusion

### Objective Outcome: **Null Result Clause Activated**
Under the pre-registered decision rules (Section 7.3 of `PREREGISTRATION.md`):
- **Method A (Phase 8 Baseline)** achieved the **lowest total CSI (4.65)**, outperforming all five candidate v2 models across Batters and Bowlers combined.
- Method A demonstrated substantially higher split-half rank stability ($\rho = 0.2887$ for batters, $\rho = 0.3772$ for bowlers) compared to Method D ($\rho = 0.1898$ and $0.2263$), because its volume saturation curves provide superior resilience against small-sample noise without overfitting to temporal sub-windows.
- In accordance with the pre-registered Null Result Clause:
  > *"Phase 8 remains superior or statistically indistinguishable under out-of-sample validation; v2 does not warrant live replacement."*

### Recommendation for Release:
1. **Primary Official Submission**: Keep the frozen **Phase 8 Official Rankings** (`output/phase8_ranking_reconsideration/`) as the default production submission.
2. **Research Appendix**: Present **Method D (v2 Pipeline)** as an advanced, auditable research framework that successfully resolves collinearity and establishes complete mathematical unity between point estimates and bootstrap confidence intervals.

---

## 6. Corrected v2 Top 10 Tables (Method D Research Benchmark)

### Official Top 10 Batters v2
| Rank | Player Name | League Evidence | Score | 90% Score CI | 90% Rank CI | P(Top 10) | Expected Rank | Balls | Matches | Tier |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | Suryakumar Yadav | IPL + T20I | 64.47 | [59.00, 68.20] | [1, 6] | 0.9870 | 2.04 | 749 | 41 | Tier 1 (N >= 300) |
| **2** | Namboori Tilak Varma | IPL + T20I | 60.01 | [54.18, 64.08] | [1, 26] | 0.7450 | 8.50 | 777 | 43 | Tier 1 (N >= 300) |
| **3** | Tim David | IPL + T20I | 59.29 | [52.86, 64.16] | [1, 38] | 0.6475 | 11.35 | 476 | 37 | Tier 1 (N >= 300) |
| **4** | Ravindra Jadeja | IPL + T20I | 58.26 | [51.81, 62.95] | [2, 44] | 0.5490 | 14.51 | 467 | 34 | Tier 1 (N >= 300) |
| **5** | Romario Shepherd | IPL + T20I | 57.39 | [51.02, 61.73] | [3, 53] | 0.4470 | 17.96 | 428 | 38 | Tier 1 (N >= 300) |
| **6** | Tristan Stubbs | IPL + T20I | 57.20 | [51.13, 61.40] | [3, 52] | 0.4010 | 18.66 | 579 | 40 | Tier 1 (N >= 300) |
| **7** | Matthew Wade | IPL + T20I | 57.02 | [49.18, 62.88] | [2, 73] | 0.3985 | 23.38 | 191 | 15 | Tier 2 (150 <= N < 300) |
| **8** | Ayush Badoni | IPL Only | 57.00 | [50.27, 61.28] | [3, 62] | 0.3745 | 20.99 | 416 | 28 | Tier 1 (N >= 300) |
| **9** | Nicholas Pooran | IPL + T20I | 56.58 | [50.75, 60.61] | [3, 55] | 0.3235 | 21.17 | 673 | 46 | Tier 1 (N >= 300) |
| **10** | Heinrich Klaasen | IPL + T20I | 55.83 | [49.64, 60.34] | [4, 69] | 0.2450 | 26.52 | 467 | 33 | Tier 1 (N >= 300) |

### Official Top 10 Bowlers v2
| Rank | Player Name | League Evidence | Score | 90% Score CI | 90% Rank CI | P(Top 10) | Expected Rank | Balls | Matches | Tier |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | Varun Chakravarthy | IPL + T20I | 61.08 | [56.53, 65.29] | [1, 11] | 0.9460 | 3.98 | 892 | 57 | Tier 1 (N >= 300) |
| **2** | Rashid Khan | IPL + T20I | 61.01 | [56.60, 65.03] | [1, 12] | 0.9355 | 4.08 | 970 | 65 | Tier 1 (N >= 300) |
| **3** | Matheesha Pathirana | IPL + T20I | 59.17 | [53.55, 64.01] | [1, 26] | 0.7595 | 8.42 | 557 | 29 | Tier 1 (N >= 300) |
| **4** | Yuzvendra Chahal | IPL + T20I | 58.55 | [53.81, 63.05] | [1, 25] | 0.7175 | 8.89 | 859 | 53 | Tier 1 (N >= 300) |
| **5** | Mitchell Santner | IPL + T20I | 58.53 | [53.27, 63.51] | [1, 28] | 0.7010 | 9.33 | 653 | 40 | Tier 1 (N >= 300) |
| **6** | Sunil Narine | IPL Only | 57.73 | [52.32, 62.77] | [1, 34] | 0.6115 | 11.97 | 511 | 35 | Tier 1 (N >= 300) |
| **7** | Jasprit Bumrah | IPL + T20I | 57.16 | [52.12, 61.74] | [2, 36] | 0.5320 | 13.42 | 606 | 44 | Tier 1 (N >= 300) |
| **8** | Bhuvneshwar Kumar | IPL + T20I | 57.00 | [52.34, 61.15] | [3, 34] | 0.5075 | 13.38 | 959 | 59 | Tier 1 (N >= 300) |
| **9** | Wanindu Hasaranga | IPL + T20I | 56.61 | [51.67, 60.75] | [3, 41] | 0.4475 | 15.36 | 639 | 41 | Tier 1 (N >= 300) |
| **10** | Mustafizur Rahman | IPL + T20I | 55.67 | [50.25, 60.37] | [3, 53] | 0.3550 | 19.92 | 527 | 41 | Tier 1 (N >= 300) |

*Invariant Verification*:
- Every point score is strictly within its 90% score CI ($100\%$ pass rate across 468 players).
- Every point rank is strictly within its 90% rank CI ($100\%$ pass rate).
- Total sum of $P(\text{Top 10})$ across all 256 eligible batters is exactly $10.0000$.
- Total sum of $P(\text{Top 10})$ across all 212 eligible bowlers is exactly $10.0000$.
- Top 10 batters capture 5.12 out of 10.0 probability mass; top 10 bowlers capture 6.51 out of 10.0.
