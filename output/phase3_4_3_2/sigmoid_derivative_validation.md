# SupeRR Intelligence — Phase 3.4.3.2 Sigmoid Mathematics Validation

**Document Status:** Completed & Validated  
**Target File:** `output/phase3_4_3_2/sigmoid_derivative_validation.md`  

---

## 1. Symbolic and Numerical Derivation

Consider the standard logistic sigmoid with slope parameter $k = 0.6$:
$$S(z) = \frac{1}{1 + e^{-0.6 z}}$$
Let $y = S(z) = \frac{1}{1 + e^{-0.6 z}}$. Then $1 - y = \frac{e^{-0.6 z}}{1 + e^{-0.6 z}}$.

### First Derivative $S'(z)$:
$$\frac{dS}{dz} = -(1 + e^{-0.6 z})^{-2} \cdot (-0.6 e^{-0.6 z}) = 0.6 \cdot \frac{1}{1 + e^{-0.6 z}} \cdot \frac{e^{-0.6 z}}{1 + e^{-0.6 z}} = 0.6 y (1 - y)$$

### Second Derivative $S''(z)$:
Applying the chain rule to $S'(z) = 0.6 (y - y^2)$:
$$\frac{d^2 S}{dz^2} = 0.6 \frac{d}{dz}[y - y^2] = 0.6 (1 - 2y) \frac{dy}{dz} = 0.6 (1 - 2y) [0.6 y (1 - y)] = 0.36 y (1 - y) (1 - 2y)$$

Expressing $1 - 2y$ in terms of exponentials:
$$1 - 2y = 1 - \frac{2}{1 + e^{-0.6 z}} = \frac{e^{-0.6 z} - 1}{1 + e^{-0.6 z}} = -\frac{1 - e^{-0.6 z}}{1 + e^{-0.6 z}}$$
Therefore, the second derivative can be written in two equivalent, exact forms:
$$S''(z) = 0.36 \cdot \frac{e^{-0.6 z} (e^{-0.6 z} - 1)}{(1 + e^{-0.6 z})^3} = -0.36 \cdot \frac{e^{-0.6 z} (1 - e^{-0.6 z})}{(1 + e^{-0.6 z})^3}$$

### Inflection Point and Curvature:
- **At $z = 0$:** $y = 0.5 \implies 1 - 2(0.5) = 0 \implies S''(0) = 0$ (**Exact Inflection Point**).
- **For $z > 0$:** $e^{-0.6 z} < 1 \implies 1 - e^{-0.6 z} > 0 \implies S''(z) < 0$ (**Strictly Concave**).
- **For $z < 0$:** $e^{-0.6 z} > 1 \implies 1 - e^{-0.6 z} < 0 \implies S''(z) > 0$ (**Strictly Convex**).

---

## 2. 100-Scaled Implementation in CPRI Engine

In the CPRI ranking codebase, adaptability is scaled to $[0, 100]$:
$$S_{100}(z) = \frac{100}{1 + e^{-0.6 z}} = 100 \cdot S(z)$$
Its derivatives are simply scaled by 100:
$$S'_{100}(z) = 60 \cdot y (1 - y)$$
$$S''_{100}(z) = 36 \cdot y (1 - y) (1 - 2y) = 36 \cdot \frac{e^{-0.6 z} (e^{-0.6 z} - 1)}{(1 + e^{-0.6 z})^3}$$

### Numerical Verification against Finite Differences:
At step size $h = 10^{-6}$:
- $z = -2.0$: $S'(z) = 0.10673666$ (analytical) vs $0.10673666$ (numerical). $S''(z) = +0.03439373$ vs $+0.03430589$.
- $z = 0.0$: $S'(0) = 0.15000000$ (analytical) vs $0.15000000$ (numerical). $S''(0) = 0.00000000$ vs $0.00000000$.
- $z = +2.0$: $S'(z) = 0.10673666$ (analytical) vs $0.10673666$ (numerical). $S''(z) = -0.03439373$ vs $-0.03419487$.

### Implementation Confirmation:
Inspection of `execute_phase3_3.py`, `execute_phase3_4_3.py`, and `supeRR_phase1_pipeline.py` confirms:
```python
sc_ad = (100.0 / (1.0 + np.exp(-0.6 * z_ad))).clip(0.0, 100.0)
```
The codebase uses the exact intended 100-scaled sigmoid with slope $k = 0.6$. The slope has not been modified.

---

## 3. Disentangling Sigmoid Curvature from Parameter Drift (Task 4)

In previous phases, the downward shift in bootstrap adaptability scores was broadly attributed to Jensen's inequality ($\mathbb{E}[S(Z)] \le S(\mathbb{E}[Z])$). However, in standard bootstrap resampling, two phenomena occur simultaneously:
1. **Nonlinear Sigmoid Curvature**: The mathematical concavity of $S_{100}(z)$ on positive $z$.
2. **Population Scale Parameter Drift**: The cohort median and IQR recompute in every draw, meaning the transformation parameters $(M^{(b)}, I^{(b)})$ are themselves random variables.

To rigorously separate these effects, we evaluated 1,000 bootstrap draws under two controlled conditions:
- **Fixed-Parameters Condition**: Median $M$ and IQR $I$ held fixed at baseline population values.
- **Recomputed-Parameters Condition**: Median and IQR recomputed dynamically in each draw.

### Exact Empirical Separation:

| Cohort | Player Name | Baseline $z$ | Baseline Adapt Score | [Fixed] Pure Jensen Effect $\mathbb{E}[S(z)] - S(\mathbb{E}[z])$ | [Fixed] Input Shift Effect $S(\mathbb{E}[z]) - S(z_{\text{base}})$ | [Fixed] Total Delta | [Recomputed] Floating Shift $\mathbb{E}[S(Z)] - S(\mathbb{E}[Z])$ | [Recomputed] Total Delta |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IPL Batters** | Rinku Singh | $3.971$ | $91.55$ | **$-2.813$ pts** | $-0.375$ pts | **$-3.188$ pts** | **$-3.049$ pts** | **$-3.260$ pts** |
| **T20I Batters** | Matthew Wade | $7.807$ | $99.08$ | **$-0.511$ pts** | $-0.103$ pts | **$-0.615$ pts** | **$-0.337$ pts** | **$+0.490$ pts** |
| **IPL Bowlers** | Matheesha Pathirana | $1.552$ | $71.73$ | **$-1.286$ pts** | $-0.567$ pts | **$-1.853$ pts** | **$-1.600$ pts** | **$+0.103$ pts** |
| **T20I Bowlers** | Sufiyan Muqeem | $3.281$ | $87.75$ | **$-4.692$ pts** | $-0.251$ pts | **$-4.943$ pts** | **$-5.595$ pts** | **$-3.005$ pts** |

### Key Insights & Formal Methodological Conclusion:
1. When population parameters are held fixed, the **pure Jensen curvature effect** accounts for $-2.813$ adaptability points ($-0.703$ CPRI) for Rinku Singh and $-4.692$ adaptability points ($-1.173$ CPRI) for Sufiyan Muqeem.
2. When parameters float, cohort IQR shrinkage can push an elite player's $z$-score higher (e.g. Matthew Wade's mean $z$ shifts from $7.81$ to $11.72$), counteracting the curvature penalty and resulting in a net positive adaptability delta ($+0.490$ pts).
3. **Formal Resolution**: A simplistic claim that Jensen's inequality explains the total CPRI drop is **officially qualified**. The drop is a joint product of min-max $s_{\max}$ denominator expansion, finite-sample peak match omission, and nonlinear sigmoid curvature.
