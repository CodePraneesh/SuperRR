# SupeRR Intelligence — Phase 3.4.3.1 Uncertainty Reporting Validation

**Document Status:** Completed & Validated  
**Target File:** `output/phase3_4_3_1/uncertainty_reporting_validation.md`  

---

## 1. Mathematical Definitions of Probability Metrics

In the SupeRR Intelligence bootstrap simulation engine, uncertainty metrics are defined under two distinct probability measures:

### A. Denominators and Probabilities:
Let $N_{\text{iterations}}$ be the total number of bootstrap iterations (e.g., 1,000).
Let $N_{\text{qualified}}$ be the number of iterations in which player $p$ satisfies the cohort eligibility criteria.
Let $N_{\text{rank}=1}$ be the number of iterations in which player $p$ is eligible and attains Rank 1.
Let $N_{\text{top10}}$ be the number of iterations in which player $p$ is eligible and attains Rank $\le 10$.

1. **Probability of Eligibility**:
   $$\mathbb{P}(\text{Eligible}) = \frac{N_{\text{qualified}}}{N_{\text{iterations}}}$$
2. **Unconditional Top 10 Probability**:
   $$\mathbb{P}(\text{Top 10}) = \frac{N_{\text{top10}}}{N_{\text{iterations}}}$$
3. **Unconditional Rank 1 Probability**:
   $$\mathbb{P}(\text{Rank} = 1) = \frac{N_{\text{rank}=1}}{N_{\text{iterations}}}$$
4. **Conditional Top 10 Probability**:
   $$\mathbb{P}(\text{Top 10} \mid \text{Eligible}) = \frac{N_{\text{top10}}}{N_{\text{qualified}}}$$
5. **Conditional Rank 1 Probability**:
   $$\mathbb{P}(\text{Rank} = 1 \mid \text{Eligible}) = \frac{N_{\text{rank}=1}}{N_{\text{qualified}}}$$

### B. Mathematical Probability Ordering:
Because a player can only achieve Rank 1 or Top 10 in iterations where they are qualified:
$$N_{\text{rank}=1} \le N_{\text{top10}} \le N_{\text{qualified}} \le N_{\text{iterations}}$$
Dividing through by $N_{\text{iterations}}$ guarantees the strict mathematical hierarchy:
$$\mathbb{P}(\text{Rank} = 1) \le \mathbb{P}(\text{Top 10}) \le \mathbb{P}(\text{Eligible})$$
This condition holds with $100\%$ compliance across all 704 player-resample records in `conditional_unconditional_uncertainty.csv`.

---

## 2. Unconditional Penalty-Rank Convention & Bimodal Nature

### Penalty-Rank Definition:
In unconditional rank evaluation, when a player does not qualify in iteration $i$, they are assigned a penalty rank:
$$\text{Rank}_i(p) = N_{\text{eligible}}^{(i)} + 1$$
where $N_{\text{eligible}}^{(i)}$ is the total number of eligible cohort players in iteration $i$.

### The Statistical Interpretation Warning:
**Penalty-adjusted unconditional rank intervals must NEVER be described as ordinary continuous confidence intervals.**

#### Case Study: Matthew Wade (T20I Batters, Match Resample):
- **Eligibility**: $\mathbb{P}(\text{Eligible}) = 86.7\%$ ($867 / 1000$ iterations).
- **Conditional Rank**: When qualified, Wade ranks between 1 and 3 in $95\%$ of iterations:
  $$\text{Conditional } 95\% \text{ Interval} = [1, 3]$$
- **Ineligible Regime**: In $13.3\%$ ($133 / 1000$) of iterations, Wade does not achieve the required threshold ($M_p < 8$ or $N_p < 100$) and receives penalty rank $\sim 85$.
- **Unconditional 95% Percentile**:
  Because $13.3\% > 2.5\%$, the $97.5^{\text{th}}$ percentile of the unconditional distribution lands on the penalty rank:
  $$\text{Unconditional } 95\% \text{ Interval} = [1, 84]$$

#### Why This Is Not a Standard Confidence Interval:
1. The unconditional rank distribution is **strongly bimodal**:
   - Mass of $86.7\%$ on ranks $\{1, 2, 3\}$.
   - Zero probability on ranks $\{4, 5, \dots, 83\}$.
   - Mass of $13.3\%$ on penalty ranks $\{84, 85, 86\}$.
2. Describing $[1, 84]$ as an ordinary confidence interval implies that Wade might be the 40th or 50th best batter in T20I cricket. In reality, he is either the #1–#3 batter when qualified, or excluded due to sampling insufficiency.
3. **Official Standard**:
   - In production reports, **always report conditional rank intervals** ($[1, 3]$) alongside the explicit probability of eligibility ($\mathbb{P}(\text{Eligible}) = 86.7\%$).
   - Unconditional rank intervals should be labeled strictly as *penalty-adjusted composite intervals*.
