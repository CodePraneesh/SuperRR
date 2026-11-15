# SupeRR Intelligence — Data Integration Plan
## High-Speed Scouting Data Layer & Feature Aggregation Specification

**Document Version:** `4.1.0`  
**Status:** Data Integration Blueprint & Schema Specification  
**Deliverable Path:** `output/phase4/data_integration_plan.md`  

---

## 1. Objective & Non-Duplication Principle

The purpose of this Data Integration Plan is to connect the raw, ball-by-ball, and ranking deliverables from Phases 1 through 3.5 into a **unified, high-speed, queryable scouting data layer** ready for real-time AI context assembly.

### The Non-Duplication Rule:
- We will **NOT** copy or duplicate the large raw files (`deliveries_enriched.csv` at $150\text{ MB}$, `pressure_scored_deliveries.csv` at $180\text{ MB}$, or expectation files at $55\text{ MB}$).
- Instead, Phase 4 will introduce an automated feature distillation pipeline that scans these datasets once and extracts compact, indexed, structured scouting tables totaling under **$8\text{ MB}$**.
- This enables sub-millisecond in-memory lookups for AI generation without reloading multi-gigabyte datasets into RAM on every query.

```
+-----------------------------------------------------------------------------------+
|                        UPSTREAM FROZEN SOURCES (PHASE 1–3.5)                      |
|                                                                                   |
|  [output/phase3_5/official_rankings.csv]   [output/phase3_3/all_batter_rankings]  |
|  [output/phase3_5/eligibility_and_uncert]  [output/phase3_3/all_bowler_rankings]  |
|  [output/processed/deliveries_enriched]    [output/phase2/delivery_wpa.csv]       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | One-Time Feature Distillation Pipeline
                                          v
+-----------------------------------------------------------------------------------+
|                  DISTILLED SCOUTING DATA STORE (output/phase4/store/)             |
|                                                                                   |
|  1. player_scouting_profiles.json   (CPRI, Components, Tiers, Uncertainty)        |
|  2. player_contextual_splits.json   (Pace/Spin, Phase P/M/D, Pressure Index)       |
|  3. head_to_head_matrix.json        (Direct Batter vs Bowler Historical Encounters)|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | In-Memory Typed Query API
                                          v
+-----------------------------------------------------------------------------------+
|                   SCOUTING QUERY API (`scouting_data_engine.py`)                  |
|                                                                                   |
|  * get_player_scouting_profile(player_name, scope)                               |
|  * get_player_splits(player_name, role, scope)                                   |
|  * get_head_to_head(batter_name, bowler_name)                                     |
|  * compare_players(player1, player2, role, scope)                                 |
|  * get_clutch_narrative_context(player_name, scope)                               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Structured Scouting Data Schemas

### A. Player Scouting Profile Store (`player_scouting_profiles.json`)
Compiled from `output/phase3_5/official_rankings.csv`, `output/phase3_5/eligibility_and_uncertainty.csv`, and `output/phase3_3/all_*_rankings.csv`.
Indexed by `(player_name, competition_scope)`:

```json
{
  "Rinku Singh": {
    "IPL": {
      "player_id": 10502,
      "player_name": "Rinku Singh",
      "competition_scope": "IPL",
      "role": "Batter",
      "ranking_tier": "Official Top 10",
      "official_rank": 1,
      "is_champion": true,
      "confidence_tier": "High Confidence",
      "cpri_score": 89.03,
      "components": {
        "pressure_impact": 100.00,
        "pressure_adaptability": 91.55,
        "clutch_consistency": 64.15,
        "reliability_confidence": 99.22
      },
      "exposure": {
        "total_deliveries": 847,
        "total_matches": 46,
        "pressure_deliveries": 269,
        "pressure_matches": 28,
        "pressure_ball_ratio": 0.318
      },
      "performance_stats": {
        "actual_runs_in_pressure": 482,
        "expected_runs_in_pressure": 371.4,
        "run_residual_in_pressure": +110.6,
        "actual_dismissals_in_pressure": 9,
        "expected_dismissals_in_pressure": 15.2,
        "dismissal_residual_in_pressure": +6.2,
        "total_wpa": +1.842,
        "pressure_wpa": +1.412,
        "positive_pressure_match_ratio": 0.642
      },
      "bootstrap_uncertainty": {
        "primary_resampling_standard": "IPL Match-Level Resampling",
        "prob_eligibility_pct": 100.0,
        "prob_rank_1_pct": 10.8,
        "prob_top10_pct": 59.7,
        "conditional_rank_median": 6,
        "conditional_rank_95_interval": [1, 46],
        "conditional_cpri_mean": 84.15,
        "conditional_cpri_sd": 7.48,
        "mc_se_r1_pct": 0.993
      }
    }
  }
}
```

---

### B. Situational Splits Store (`player_contextual_splits.json`)
Compiled by grouping `output/processed/deliveries_enriched.csv` by player and situational dimensions:

#### 1. Bowling Type Split (Pace vs. Spin):
- Metrics tracked separately against `Pace` and `Spin`:
  * Balls faced, runs scored, dismissals.
  * Strike Rate ($SR = 100 \cdot \text{Runs} / \text{Balls}$).
  * Dot ball percentage ($\text{Dots} / \text{Balls}$).
  * Boundary rate (balls per boundary).
  * Balls per dismissal ($BPD$).

#### 2. Innings Phase Split:
- **Powerplay (Overs 1–6):** Early overs anchoring, boundary striking against field restrictions.
- **Middle Overs (Overs 7–15):** Rotation of strike, spin tackling, wicket preservation.
- **Death Overs (Overs 16–20):** High-leverage execution, boundary frequency, yorker handling.

#### 3. Pressure Contrast Split:
- High Pressure ($\text{Pressure Index} \ge 50.0$) vs. Non-Pressure ($\text{Pressure Index} < 50.0$):
  * Quantifies whether a player's strike rate and survival improve or degrade under game pressure.

```json
{
  "Rinku Singh": {
    "IPL": {
      "pace_vs_spin": {
        "pace": {"balls": 482, "runs": 718, "outs": 14, "sr": 148.96, "dot_pct": 28.4, "boundary_pct": 19.5},
        "spin": {"balls": 365, "runs": 492, "outs": 8, "sr": 134.79, "dot_pct": 33.2, "boundary_pct": 14.8}
      },
      "innings_phase": {
        "powerplay": {"balls": 45, "runs": 52, "outs": 1, "sr": 115.56, "dot_pct": 42.2},
        "middle": {"balls": 382, "runs": 498, "outs": 9, "sr": 130.37, "dot_pct": 32.7},
        "death": {"balls": 420, "runs": 660, "outs": 12, "sr": 157.14, "dot_pct": 26.9, "pressure_sr": 164.2}
      },
      "pressure_contrast": {
        "high_pressure_sr": 154.6,
        "low_pressure_sr": 136.2,
        "delta_sr": +18.4,
        "high_pressure_dot_pct": 27.5,
        "low_pressure_dot_pct": 33.1
      }
    }
  }
}
```

---

### C. Head-to-Head Batter vs. Bowler Matrix (`head_to_head_matrix.json`)
Aggregated from `deliveries_enriched.csv` grouping by `(striker_name_clean, bowler_name_clean)`:
- Balls faced.
- Runs scored.
- Dismissals (credited bowler wickets).
- Dot balls.
- Fours and Sixes.
- Average Pressure Index during matchup.
- Historical Strike Rate & Balls per Dismissal.

```json
{
  "Rinku Singh vs Mohit Sharma": {
    "batter": "Rinku Singh",
    "bowler": "Mohit Sharma",
    "competition_scope": "IPL",
    "balls_faced": 26,
    "runs_scored": 48,
    "dismissals": 1,
    "dot_balls": 6,
    "fours": 3,
    "sixes": 4,
    "strike_rate": 184.62,
    "avg_pressure_index": 72.4,
    "tactical_assessment": "High-scoring matchup under extreme death pressure; batter scores freely at 184.6 SR with 7 boundary events in 26 balls."
  }
}
```

---

## 3. High-Speed Query API Design (`scouting_data_engine.py`)

A clean, modular Python service interface providing typed access to all scouting features:

```python
class ScoutingDataEngine:
    def __init__(self, data_dir: Path):
        self.profiles = load_profiles(data_dir / 'player_scouting_profiles.json')
        self.splits = load_splits(data_dir / 'player_contextual_splits.json')
        self.h2h = load_h2h(data_dir / 'head_to_head_matrix.json')

    def get_player_scouting_profile(self, player_name: str, scope: str = 'IPL') -> dict | None:
        """Retrieves official CPRI, components, exposure, and bootstrap uncertainty."""

    def get_player_splits(self, player_name: str, role: str, scope: str = 'IPL') -> dict | None:
        """Retrieves pace/spin, phase (PP/Mid/Death), and pressure contrast metrics."""

    def get_head_to_head(self, batter_name: str, bowler_name: str) -> dict | None:
        """Retrieves direct historical encounter stats between two specific athletes."""

    def compare_players(self, player1: str, player2: str, role: str, scope: str = 'IPL') -> dict:
        """Produces a side-by-side comparative dictionary of CPRI metrics and splits."""

    def get_clutch_narrative_context(self, player_name: str, scope: str = 'IPL') -> str:
        """Assembles a verified, structured prompt context string for LLM injection."""
```

---

## 4. Factual Grounding & Prompt Formatting Protocol

To guarantee zero hallucination, the prompt generator formats facts into strict, unambiguous markdown tables with explicit negative constraints:

```markdown
### VERIFIED SCOUTING RECORD (GROUND TRUTH)
- Player: Rinku Singh
- Format: IPL
- Role: Batter
- Official CPRI Score: 89.03 (Rank: #1, High Confidence)
- Components: Impact=100.00, Adaptability=91.55, Consistency=64.15, Reliability=99.22
- Sample Exposure: 269 pressure deliveries across 28 pressure matches
- Situational Splits:
  * Death Overs (16-20): Strike Rate 157.14, Boundary Frequency: 18.2%
  * Pace vs Spin: 148.96 SR vs Pace (14 outs) | 134.79 SR vs Spin (8 outs)
  * Pressure Contrast: +18.4 SR increase under high pressure (Pressure Index >= 50)
- Bootstrap Stability: Conditional 95% Rank Interval: [1, 46], Eligibility Prob: 100.0%

[INSTRUCTION]: Explain this player's performance based ONLY on the numbers above.
Never invent statistics. Never propose a new rank.
```

---
*Signed and Approved for Phase 4 Implementation.*
