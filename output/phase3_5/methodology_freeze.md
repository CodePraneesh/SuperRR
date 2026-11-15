# SupeRR Intelligence — CPRI Production Methodology Freeze Specification

**Methodology Version:** `CPRI-v1.0.0-PROD-FREEZE`  
**Freeze Timestamp:** `2026-11-14T20:55:00+05:30`  
**Official Verdict:** **FREEZE APPROVED WITH DOCUMENTED LIMITATIONS**  
**Target Directory:** `output/phase3_5/`  

---

## 1. Frozen CPRI Mathematical Architecture

The Clutch Performance Rating Index (CPRI) is a composite index bounded in $[0, 100]$ evaluating individual cricketer performance strictly under high-pressure game situations.

$$\text{CPRI} = 0.40 \cdot \text{Impact} + 0.25 \cdot \text{Adaptability} + 0.20 \cdot \text{Consistency} + 0.15 \cdot \text{Reliability}$$

### Component Definitions & Normalization:
1. **Pressure Impact (Weight: $0.40$):**
   - Delivery-level net impact is defined as:
     * Batters: $\text{Residual Runs} + 12.0 \cdot \text{Residual Survival} + 25.0 \cdot \text{Batting WPA}$
     * Bowlers: $\text{Residual Conceded Runs} + 12.0 \cdot \text{Residual Wickets} + 25.0 \cdot \text{Bowling WPA}$
   - Aggregated per 100 pressure balls and shrunk towards cohort mean via Bayesian shrinkage ($m = 40.0$).
   - Scaled using linear min-max normalization to $[0, 100]$: $\text{Impact} = 100 \cdot \frac{I_p - s_{\min}}{s_{\max} - s_{\min}}$.
2. **Pressure Adaptability (Weight: $0.25$):**
   - Raw performance difference: $\Delta \text{Impact} = \text{Pressure Net Impact Rate} - \text{Non-Pressure Net Impact Rate}$.
   - Shrunk via Bayesian shrinkage ($m = 40.0$) using effective sample size $\min(N_{\text{pressure}}, N_{\text{nonpressure}})$.
   - Standardized via robust $z$-score: $z = \frac{A_p - \text{median}(A)}{\text{IQR}(A) / 1.349}$.
   - Scaled using the robust logistic sigmoid function with slope $k = 0.6$:
     $$S_{100}(z) = \frac{100}{1 + e^{-0.6 z}}$$
3. **Clutch Consistency (Weight: $0.20$):**
   - Evaluates match-to-match reliability under pressure using the positive pressure match ratio:
     $$\text{Raw Consistency} = 50.0 \cdot \frac{M_{\text{positive}}}{M_{\text{pressure}}} + 35.0$$
   - Shrunk via Bayesian shrinkage ($m = 5.0$) and scaled using linear min-max normalization to $[0, 100]$.
4. **Reliability Confidence (Weight: $0.15$):**
   - Two-dimensional exponential saturation accounting for pressure ball and match exposure:
     $$R_p = 100 \cdot \left(1 - e^{-B_p / 60.0}\right) \cdot \left(1 - e^{-M_p / 5.0}\right)$$
   - Strictly bounded in $[0, 100]$ and monotonic in exposure.

---

## 2. Invariant Thresholds & Eligibility Standards

### A. Pressure Threshold: $\ge 50.0$
A delivery is classified as high-pressure if and only if the ball-by-ball Pressure Index satisfies $\text{Pressure Score} \ge 50.0$. Super overs (innings $\ge 3$) and emerging team matches are excluded.

### B. Cohort Isolation:
All calculations, Bayesian priors, median/IQR scales, and min-max bounds are calculated strictly independently within each cohort. Zero cross-cohort normalization is permitted.

### C. Minimum Qualification Criteria:
- **Batters (Official Cohort):**
  * Pressure balls faced: $N_p \ge 100$
  * Pressure matches played: $M_p \ge 8$
  * Total balls faced: $N_{\text{tot}} \ge 150$
  * Non-pressure balls faced: $N_{\text{np}} \ge 40$
- **Bowlers (Official Cohort):**
  * Pressure balls bowled: $N_p \ge 80$
  * Pressure matches played: $M_p \ge 8$
  * Total balls bowled: $N_{\text{tot}} \ge 180$
  * Balls per match rate: $\text{bpm} \ge 12.0$ (at least 2 overs per match)

### D. Separation of Provisional Rankings:
Players with $40 \le N_p < 100$ (batters) or $30 \le N_p < 80$ (bowlers) are tagged as *Moderate Confidence* and ranked exclusively in separate **Provisional Top 5** tables. They are permanently excluded from the Official Top 10.

---

## 3. Resampling & Uncertainty Standards

### Resampling Protocols:
1. **IPL Resampling Standard:** Match-level clustered bootstrap is the frozen primary standard. Annual season block resampling is preserved strictly as a coarse sensitivity check due to the statistical constraint of having only $K = 5$ season clusters ($(4/5)^5 \approx 32.8\%$ omission probability).
2. **T20I Resampling Standard:** Series-level cluster bootstrap using official competition IDs (`comp_id`) across 131 international tours/tournaments is the frozen primary standard, preserving bilateral series integrity.

### Distinction of Error Measures:
- **Monte Carlo Simulation Error ($SE_{MC}$):** Numerical approximation error due to drawing $N$ iterations ($SE_{MC} \le 0.70\%$ at $N = 5,000$).
- **Cricket Performance Statistical Uncertainty:** Real-world sampling variance across matches, reflected by player CPRI standard deviation ($2.18$ to $11.02$ points) and conditional rank intervals.
- **Probability Hierarchy:** Mathematical constraint strictly verified:
  $$\mathbb{P}(\text{Rank} = 1) \le \mathbb{P}(\text{Top 10}) \le \mathbb{P}(\text{Eligible})$$

---

## 4. AI Immutability & Anti-Tampering Guarantee

> [!IMPORTANT]
> **FROZEN PRODUCTION COVENANT:**
> 1. CPRI point estimates, component scores, and official rankings in `output/phase3_5/` are deterministic mathematical constants.
> 2. No future AI model, downstream analytical agent, or natural language interface may modify, recalculate, or perturb these official scores or rankings.
> 3. AI commentary must present official rankings as deterministic facts, accompanied by their documented conditional rank uncertainty bands.

---

## 5. Frozen Official Top 10 Champions

- **IPL Batter Champion:** **Rinku Singh** (CPRI: **89.03**, Rank: **1**)
- **T20I Batter Champion:** **Matthew Wade** (CPRI: **97.42**, Rank: **1**)
- **IPL Bowler Champion:** **Matheesha Pathirana** (CPRI: **83.50**, Rank: **1**)
- **T20I Bowler Champion:** **Sufiyan Muqeem** (CPRI: **86.44**, Rank: **1**)
