# SupeRR Intelligence — Phase 3.4.3.1 Jensen's Inequality Verification

**Document Status:** Completed & Validated  
**Target File:** `output/phase3_4_3_1/jensen_inequality_verification.md`  

---

## 1. Mathematical Framework of Robust Sigmoid Adaptability

In the CPRI engine, player adaptability is transformed using a robust sigmoid function:
$$S(z) = \frac{100}{1 + e^{-0.6 z}}$$
where $z = \frac{A_p - \text{median}(A)}{\text{IQR}(A) / 1.349}$, and $A_p$ is Bayesian shrunk adaptability.

### Derivatives and Curvature:
Let $y = \frac{1}{1 + e^{-0.6 z}}$. The first and second derivatives of $S(z)$ with respect to $z$ are:
$$S'(z) = 60 \cdot y(1 - y) > 0 \quad \forall z$$
$$S''(z) = 36 \cdot y(1 - y)(1 - 2y)$$

Evaluating the sign of $S''(z)$:
- At $z = 0$: $y = 0.5 \implies 1 - 2y = 0 \implies S''(0) = 0$ (**Inflection Point**).
- For $z > 0$: $y > 0.5 \implies 1 - 2y < 0 \implies S''(z) < 0$ (**Strictly Concave**).
- For $z < 0$: $y < 0.5 \implies 1 - 2y > 0 \implies S''(z) > 0$ (**Strictly Convex**).

By **Jensen's Inequality**:
- If a random variable $Z$ lies entirely in the concave region ($Z > 0$ almost surely), then:
  $$\mathbb{E}[S(Z)] \le S(\mathbb{E}[Z])$$
  producing a downward shift $\mathbb{E}[S(Z)] - S(\mathbb{E}[Z]) \le 0$.
- If $Z$ crosses the inflection point $z = 0$, both concave ($z > 0$) and convex ($z < 0$) regions contribute to $\mathbb{E}[S(Z)]$, meaning Jensen's inequality cannot be applied as a simple one-sided bound.

---

## 2. Empirical Verification on Actual Bootstrap Draws

Using 1,000 bootstrap draws across the official cohorts, we tracked the empirical distribution of $z$-scores and the exact value of $S(z)$ for the focal players:

| Cohort | Player Name | Mean $z$ | Std $z$ | Min $z$ | Max $z$ | Crosses $z \le 0$ (%) | $\mathbb{E}[S(Z)]$ | $S(\mathbb{E}[Z])$ | Jensen Shift (Adaptability pts) | CPRI Impact ($0.25 \times \text{Shift}$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IPL Batters** | Rinku Singh | $3.926$ | $1.660$ | $-1.212$ | $10.909$ | **1.0%** | $88.29$ | $91.34$ | **$-3.05$** | **$-0.762$ pts** |
| **T20I Batters** | Matthew Wade | $11.719$ | $4.135$ | $4.017$ | $44.517$ | **0.0%** | $99.57$ | $99.91$ | **$-0.34$** | **$-0.084$ pts** |
| **IPL Bowlers** | Matheesha Pathirana | $1.694$ | $1.032$ | $-1.166$ | $6.189$ | **3.7%** | $71.83$ | $73.43$ | **$-1.60$** | **$-0.400$ pts** |
| **T20I Bowlers** | Sufiyan Muqeem | $3.725$ | $2.253$ | $-3.962$ | $11.611$ | **4.5%** | $84.74$ | $90.34$ | **$-5.60$** | **$-1.399$ pts** |

---

## 3. Findings & Corrective Conclusion

1. **Inflection Point Crossing Verified**:
   - For Rinku Singh ($1.0\%$), Matheesha Pathirana ($3.7\%$), and Sufiyan Muqeem ($4.5\%$), the bootstrap distribution of $z$-scores **crosses the inflection point ($z=0$)** into the convex region.
   - For Matthew Wade, all draws remain in the concave region ($z \ge 4.017$).
2. **Correction of the '< 0.25 CPRI Points' Claim**:
   - The Phase 3.4.3 report claimed that Jensen's inequality produces a downward shift of $< 0.25$ CPRI points.
   - Our empirical audit demonstrates that this claim is **FALSE for 3 of the 4 focal players**:
     * Rinku Singh: Shift = **$-0.762$ CPRI points** (more than 3 times 0.25).
     * Matheesha Pathirana: Shift = **$-0.400$ CPRI points**.
     * Sufiyan Muqeem: Shift = **$-1.399$ CPRI points** (more than 5.5 times 0.25).
     * Only Matthew Wade exhibited an impact $< 0.25$ points ($-0.084$ CPRI points), because his mean $z = 11.72$ is far out on the asymptotic saturation plateau where $S'(z) \approx 0$ and $S''(z) \approx 0$.
3. **Formal Correction**:
   - We **explicitly withdraw the blanket claim of < 0.25 points**.
   - The actual empirical Jensen shift accounts for $-0.40$ to $-1.40$ CPRI points in high-variance players, which is a meaningful component of the overall bootstrap downward shift alongside min-max normalization inflation.
