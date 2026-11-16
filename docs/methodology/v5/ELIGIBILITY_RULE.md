# Eligibility Rule: Recent Activity in the Supplied Match Data

**Document Reference**: `RULE-ELIGIBILITY-v5`  
**Status**: Formal Specification of Supplementary Active View  
**Author**: SupeRR Intelligence Analytics Team  
**Date**: November 16, 2026  

---

## 1. Operational Definition

A player is defined as **"Recently active in the dataset"** if and only if:

$$\text{Player has } \ge 1 \text{ delivery in the supplied ball-by-ball dataset, in the ranked role, in a match dated on or after } (T_{\max} - 12 \text{ months})$$

Where:
- $T_{\max}$ is the maximum match date present in the supplied in-scope dataset, computed directly from data records (computed as `2026-11-01 00:00:00+00:00`), never hand-typed.
- **Ranked Role**: The delivery must be executed in the evaluated role:
  - For the **Batter** leaderboard: The player participated as the **striker** (`striker_id == player_id`).
  - For the **Bowler** leaderboard: The player participated as the **bowler** (`bowler_id == player_id`).
- **Primary Eligibility Window**: Exactly 12 calendar months prior to $T_{\max}$ (effective threshold: matches dated on or after `2025-11-01 00:00:00`).

---

## 2. In-Scope Competitions & Scope Boundaries

1. **Identical Competition Scope**: The eligibility assessment operates exclusively over the official in-scope competitions established in Phase 8:
   - Indian Premier League (IPL)
   - Senior Men's Twenty20 Internationals (T20Is) between ICC Full Members and top-tier associate fixtures.
2. **Strict Availability Caveat**: A player who has not appeared in this specific dataset within the 12-month window may remain actively contracted and competing in other domestic, regional, or overseas franchise leagues (e.g., Big Bash League, Caribbean Premier League, Pakistan Super League, SA20, Vitality Blast).
3. **Mandatory Non-Retirement Labeling**: Consequently, absence from recent matches in this dataset represents solely that the player is:
   $$\text{"not recently active in the supplied data"}$$
   Under no circumstances is a player labeled as *"retired"*, as retirement is an external administrative status outside the scope of the provided data.

---

## 3. Methodological Governance: Post-Hoc Status & Uniform Application

1. **Post-Hoc Rule Declaration**: This eligibility filter is a **post-hoc eligibility rule** introduced after analyzing the frozen Phase 8 competition rankings (where historical contributors like Matthew Wade ranked #1 based on cumulative dataset sample depth). It is explicitly **not** a pre-registered methodology rule.
2. **Zero Player-Name Logic**: The 12-month window is chosen as a standard, round annual calendar interval and applied 100% uniformly across all players in the population. No exemptions, overrides, or manual player-specific inclusion/exclusion logic are permitted.
3. **Sensitivity Analysis**: To verify that ranking movements are not an artifact of an arbitrary 12-month boundary, sensitivity evaluations are conducted at alternative window lengths:
   - **6-Month Window** (Threshold: matches dated on or after `2026-05-01`)
   - **18-Month Window** (Threshold: matches dated on or after `2025-05-01`)
   
   These sensitivity windows provide transparent auditing context but do not alter the primary 12-month rule.
4. **Decoupled Baseline Preservation**: The official Phase 8 submission (`output/phase8_ranking_reconsideration/`) remains the permanent, frozen competition baseline. This active-only view is strictly a supplementary eligibility view.
