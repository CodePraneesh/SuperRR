# SupeRR Intelligence: Pre-Registration Document (Phase 11 v3)
## Pressure Definition Validation, Challenger Formulations & Decision Gate Protocol

**Project**: SupeRR Intelligence (SupeRR Selector Season 2, Round 1)  
**Date**: November 15, 2026  
**Status**: PRE-REGISTERED (Committed BEFORE computing any challenger ranking)  
**Author**: Sports Analytics Research & Engineering Team  
**Evaluation Scope**: 883 Matches, 194,014 In-Scope Deliveries (IPL + T20I)  
**Random Seed**: 42 (Fixed) | **Bootstrap Replicates**: 1,000 Match-Cluster Draws  

---

## 1. Context and Motivation

An independent audit of the frozen Phase 8 pressure definition identified substantial structural limitations in the Phase 2 learned pressure model (Finding F3):
- **High Lopsidedness**: 31.8% of in-scope deliveries are flagged as "pressure" ($PI \ge 50$). In the 2nd innings, the mean batting side win probability on flagged balls is only $0.179$, with $61.01\%$ of flagged balls being lopsided ($P_{\text{win}} < 0.15$ or $> 0.85$).
- **Low Contested Share**: Only $15.70\%$ of flagged deliveries fall into the genuinely contested win probability zone ($0.35 \le P_{\text{win}} \le 0.65$).
- **Weak Leverage Correlation**: The correlation between the pressure score and delivery leverage ($\text{corr}(PI, |\text{delivery WPA}|)$) is only $0.0488$.
- **Non-Monotonic Tiers**: The "Extreme" tier exhibits a *lower* mean $|\text{WPA}|$ ($0.0050$) than the "High" ($0.0071$) and "Moderate" ($0.0075$) tiers.
- **Innings Imbalance**: $46.30\%$ of 2nd-innings powerplay deliveries are flagged as pressure, compared to only $2.42\%$ in the 1st innings.
- **Role Asymmetry**: The same pressure score is applied to both batters and bowlers, despite a lost run chase representing zero pressure for the defending bowler.
- **Environment Sensitivity (Finding F1)**: Because the pressure score derives from learned gradient-boosted trees and ridge regression models, minor numerical variations across library versions (e.g., scikit-learn 1.9.1 / pandas 3.0.5 vs pinned scikit-learn 1.8.0 / pandas 2.3.3) shift predictions on borderline balls near $PI=50$ by 1–5 balls, perturbing CPRI scores and swapping adjacent ranks.

To address these empirical findings, this document pre-registers three challenger pressure definitions, explicit validation criteria, and a strict, mechanical decision gate.

---

## 2. Pre-Registered Pressure Definitions

To ensure fair comparison, all challenger definitions normalize their threshold so that exactly the top **20.0%** of deliveries ($\sim 38{,}800$ balls) are designated as pressure.

### Definition A (Baseline — Phase 8 Frozen)
- Formulation: Phase 2 learned composite pressure index $PI \ge 50.0$.
- Deliveries flagged: 61,719 (31.81% of in-scope balls).
- Nature: Learned gradient-boosted / regression model.

### Definition B (Challenger 1 — Role-Aware Expected Leverage, $EL$)
- Formulation: Measures the magnitude of game-outcome leverage at stake on the delivery:
  $$EL_i = |\Delta P_{\text{win}, i}| = |P_{\text{win, after}, i} - P_{\text{win, before}, i}|$$
- Role-Awareness:
  - For batters: acute when batting team win probability can swing substantially ($0.20 \le P_{\text{win}} \le 0.80$). Hopeless chases ($P_{\text{win}} < 0.05$) have $EL \approx 0$.
  - For bowlers: acute when bowler's delivery can alter the opponent's chances. Defending a 10-run required rate with 1 over remaining has near-zero bowler leverage because the match is effectively decided.
- Threshold: Top 20% by delivery leverage ($EL \ge q_{0.80}(EL)$).

### Definition C (Challenger 2 — Closed-Form Contest Closeness $\times$ Balls Remaining, $CCBR$)
- Formulation: A completely model-free, closed-form mathematical expression that eliminates machine-learning library sensitivity:
  $$\text{Contest Closeness} = 1.0 - 2 \cdot |P_{\text{win}} - 0.50|$$
  $$\text{Urgency Factor} = 1.0 + \frac{120 - \text{balls\_remaining}}{120}$$
  $$CCBR = (1.0 - 2 \cdot |P_{\text{win}} - 0.50|) \times \left(1.0 + \frac{120 - \text{balls\_remaining}}{120}\right)$$
- Properties: Strictly peaks when matches are evenly poised ($P_{\text{win}} = 0.50$) in late overs; drops to zero for blowouts regardless of phase.
- Threshold: Top 20% by $CCBR$ score ($CCBR \ge q_{0.80}(CCBR)$).

### Definition D (Challenger 3 — Contest Leverage with Knockout Multiplier, $ELK$)
- Formulation: Definition B augmented by tournament stage context:
  $$ELK_i = EL_i \times \text{Stage Weight}$$
  where $\text{Stage Weight} = 1.25$ for knockout fixtures (Final, Qualifier, Eliminator, Semi-Final) and $1.00$ for group matches.
- Threshold: Top 20% by $ELK$.

---

## 3. Pre-Registered Validation Criteria

Each pressure definition will be evaluated on five pre-registered criteria:

| Criterion | Definition | Ideal Direction | Baseline (Phase 8) |
| :--- | :--- | :---: | :---: |
| **$V_1$: Mean Absolute Leverage** | $\mathbb{E}[\|\text{delivery WPA}\|]$ on pressure vs ordinary | Higher in pressure | $0.0062$ vs $0.0053$ ($\Delta = +0.0009$) |
| **$V_2$: Contested Share** | $\% \text{ flagged balls with } 0.35 \le P_{\text{win}} \le 0.65$ | Higher (target $> 40\%$) | $15.70\%$ |
| **$V_3$: Innings Balance Ratio** | Ratio of 1st-innings to 2nd-innings pressure balls | Balanced ($0.70 \le \text{ratio} \le 1.30$) | $0.31$ (14,706 vs 46,987) |
| **$V_4$: Tier Monotonicity** | Mean $\|\text{WPA}\|$ strictly ordered: Extreme $>$ High $>$ Moderate $>$ Low | Strictly monotonic | Violates (Extreme $0.0050 <$ High $0.0071$) |
| **$V_5$: Environment Invariance** | Rank stability across scikit-learn/pandas versions | Identical ranks | Shifts by 1–5 balls (ranks swap) |

---

## 4. Mechanical Decision Gate

In accordance with strict research integrity, the decision to recommend replacing the frozen Phase 8 submission with a challenger definition will be governed by the following mechanical gate:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              PRE-REGISTERED DECISION GATE                              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  A challenger pressure definition will ONLY be recommended for live submission if:     │
│                                                                                        │
│  1. VALIDITY CRITERIA: It strictly outperforms Definition A on V1, V2, and V4,         │
│     with 95% bootstrap confidence intervals for the improvement excluding zero.       │
│                                                                                        │
│  2. RANKING STABILITY: The resulting player rankings achieve bootstrap rank CI         │
│     widths and split-half reliability equal to or better than Phase 8.                 │
│                                                                                        │
│  3. ENVIRONMENT REPRODUCIBILITY: The ranking is 100% invariant to library version      │
│     changes (exact reproducibility under both requirements.lock and latest libraries). │
│                                                                                        │
│  IF ANY CONDITION FAILS:                                                               │
│     -> Retain Phase 8 as the official submission.                                      │
│     -> Report the challenger strictly as a Sensitivity Analysis.                       │
│     -> Output a 25-player robustness table showing selection stability across all      │
│        defensible definitions.                                                         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Ranking Framework and Tie-Breaking Rules

All challenger rankings will be computed using the identical CPRI structural architecture:
- Pressure Impact ($40\%$), Adaptability ($25\%$), Consistency ($20\%$), Reliability ($15\%$).
- Match-cluster bootstrap (1,000 draws, seed=42) resampling entire matches.
- Eligibility threshold: $N \ge 60$ pressure balls, $M \ge 5$ pressure matches.
- Deterministic 5-tuple tie-breaking:
  $$\text{Key} = (\text{Score}, P(\text{Top 10}), \text{Pressure Deliveries}, \text{Pressure Matches}, \text{Player ID})$$

---

## 6. Commitment

No challenger rankings have been computed prior to the git commit of this file. The decision gate will be executed mechanically without outcome-driven adjustments.
