# Phase 8: Dynamic Pressure Definition & Sensitivity Audit

## 1. Mathematical Formulation from First Principles
A delivery's pressure score evaluates the **contextual demand / match leverage** placed on the players at that exact moment.

### Core Anti-Leakage Constraints
1. **Zero Lookahead**: All input features are computed using only match events occurring *prior* to the delivery (via `shift(fill_value=0)`).
2. **Zero Outcome Leakage**: A boundary or wicket never retroactively influences the pressure classification of the ball on which it occurred.
3. **Zero Target Leakage**: Future match results are strictly excluded.

### Innings 1: Economic Maximization Regime
First-innings pressure evaluates resource depletion relative to par score:
$$\text{PI}_{1} = 0.35 \times \text{ParDeficit} + 0.35 \times \text{WicketScarcity} + 0.20 \times \text{PhaseUrgency} + 0.10 \times \text{ScoringDrag}$$
Where:
- Par score is anchored to format standards (186.0 for IPL, 171.0 for T20I).
- Wicket scarcity scales super-linearly: $(1.0 - \text{wickets\_in\_hand} / 10.0)^{1.5}$.

### Innings 2: Deterministic Target Chase
Second-innings pressure evaluates required run rate escalation and ball exhaustion:
$$\text{PI}_{2} = 0.45 \times \tanh\left(\left(\frac{\text{RRR}}{14.0}\right)^{1.3}\right) + 0.30 \times \text{BallDepletion} + 0.25 \times \text{WicketDepletion}$$

## 2. Sensitivity Analysis across Thresholds
| Pressure Threshold | In-Scope Deliveries | % of Total Deliveries | Cricket Interpretation |
|---|---|---|---|
| **PI $\ge$ 40.0** | 79782 | 41.1% | Broad definition including early middle-overs urgency |
| **PI $\ge$ 50.0 (Benchmark)** | 61719 | 31.8% | Balanced clutch definition: high leverage match situations |
| **PI $\ge$ 60.0** | 44363 | 22.9% | High-crisis definition: steep chases & late-order defense |

## 3. Why Pressure is Distinct from Death Overs
- Death-over bowling in a blowout match (e.g. defending 230 when opponents are 120/8 needing 25 RPO) has low leverage ($PI < 35$).
- Powerplay or middle-overs bowling when defending a low total (e.g. 130) with top batters at the crease has intense leverage ($PI > 65$).
- Our model captures genuine situational tension rather than blind over-segmentation.
