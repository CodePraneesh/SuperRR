# SupeRR Intelligence — Phase 3.4.3.2 Test Coverage and Statistical Limitations

**Document Status:** Completed & Validated  
**Target File:** `output/phase3_4_3_2/test_coverage_and_limitations.md`  

---

## 1. Test Suite Coverage Summary

The SupeRR Intelligence test suite comprises **114 automated unit tests** across all phases:
- **Phase 1 Validation Tests (16 tests):** Verify strict 5-point dismissal specifications, legal ball accounting, bowler credited wickets, cumulative zero-leakage state progression, and strict IPL/T20I cohort separation.
- **Phase 2A / 2B / 2C Expectations & WPA Tests (44 tests):** Verify expected run and dismissal bounds, Bayesian shrinkage directions, WPA bounds $[-1, 1]$, and boundary/death-over monotonicities.
- **Phase 3 & 3.1 Ranking Engine Tests (26 tests):** Verify player consistency formulas, reliability scaling, CPRI score bounds $[0, 100]$, and duplicate player elimination.
- **Phase 3.2 & 3.3 Robust Normalization Tests (10 tests):** Verify robust sigmoid scaling properties, Matthew Wade audit facts, and revised Top 10 rankings integrity.
- **Phase 3.4 & 3.4.1 Resampling Tests (10 tests):** Verify match-level resampling, eligibility tracking, and cohort isolation.
- **Phase 3.4.3 & 3.4.3.1 Statistical Integrity Tests (8 tests):** Verify 1,000-iteration reconciliation, $2 \times 2$ factorial math, Jensen inflection point crossing, and probability hierarchies.

### Exact What-It-Verifies Test Mapping:

| Test Suite File | Test Function | What It Actually Verifies | Statistical Limitation Not Captured |
| :--- | :--- | :--- | :--- |
| `test_cpri_32.py` | `test_03_robust_adaptability_scaling_properties` | Monotonicity and $[0, 100]$ bounds of $S(z)$. | Does not guarantee that bootstrap mean matches point estimate. |
| `test_phase3_4_3_1.py` | `test_04_factorial_decomposition_metrics` | Arithmetic correctness of ANOVA formulas. | Does not eliminate the physical omission of peak matches. |
| `test_phase3_4_3_1.py` | `test_05_jensen_inequality_inflection_and_shift` | Inflection point crossing ($z \le 0$) and numerical shifts. | Does not alter sigmoid concavity for positive $z$. |
| `test_phase3_4_3_1.py` | `test_07_uncertainty_reporting_probability_ordering` | Strict hierarchy $P(R=1) \le P(T10) \le P(\text{Elig})$. | Does not force bimodal penalty ranks to be unimodal. |

> [!IMPORTANT]
> Passing unit tests confirms **software implementation correctness and arithmetic integrity**, not the absence of underlying real-world sampling variability.

---

## 2. Documented Methodological Limitations for Phase 3.5 Freeze

The following statistical limitations are permanently documented and accepted under the **APPROVED WITH DOCUMENTED LIMITATIONS** classification:

### Limitation 1: IPL Season Cluster Sparsity ($K = 5$)
- The IPL historical corpus spans exactly 5 seasons (2022–2026, 371 matches). Resampling seasons with replacement results in a $32.8\%$ omission probability for any specific season.
- **Standard:** Match-level resampling is the mandatory primary statistical standard for IPL cohorts.

### Limitation 2: Selection Regression in Standout Performers
- Standout players who achieved exceptional baseline ratings in small-to-moderate sample sizes (e.g. Ashutosh Sharma, 187 balls; Sufiyan Muqeem, 90 balls) inevitably regress downward under bootstrap resampling because their standout games are omitted with probability $1/e \approx 36.8\%$.
- **Standard:** Point estimates determine official ranks; bootstrap distributions determine uncertainty bands.

### Limitation 3: Bimodal Nature of Unconditional Penalty Ranks
- Players with eligibility probabilities between $65\%$ and $95\%$ exhibit bimodal unconditional rank distributions (mass on peer ranks $[1, 10]$ and mass on penalty rank $N_{\text{eligible}} + 1$).
- **Standard:** Production outputs must always display the **conditional rank interval** alongside the explicit **eligibility probability**.
