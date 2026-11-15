#!/usr/bin/env python3
"""
scouting_data_engine.py
SupeRR Intelligence - Phase 4.3 Scouting Data Engine

Provides a high-speed, queryable service over the frozen Phase 4.2 scouting stores:
1. player_scouting_profiles.json
2. player_contextual_splits.json
3. head_to_head_matrix.json

Strictly adheres to:
- CPRI-v1.0.0-PROD-FREEZE (Phase 3.5 Frozen Baseline)
- Complete format segregation (IPL and T20I never combined)
- Authoritative CPRI component mapping (Pressure Impact, Adaptability, Consistency, Reliability)
- Separation of frozen match-state pressure deliveries from striker balls faced
- Resilience to missing players and small-sample warnings
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "output" / "phase4" / "data"


class ScoutingDataEngine:
    """
    In-memory scouting data engine providing high-speed retrieval,
    peer benchmarking, head-to-head matchups, and situational splits.
    """

    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.profiles_store = self._load_json("player_scouting_profiles.json")
        self.splits_store = self._load_json("player_contextual_splits.json")
        
        # Lazy-loaded to conserve RAM and optimize startup latency
        self._h2h_store: Optional[Dict[str, Any]] = None
        self._h2h_by_key: Optional[Dict[str, Any]] = None
        
        # Load official Phase 8 unified store if present
        off_file = self.data_dir / "official_scouting_store.json"
        self.official_store = self._load_json("official_scouting_store.json") if off_file.exists() else {}

        # Fast in-memory indexes
        self._profiles_by_key = self.profiles_store.get("by_key", {})
        self._profiles_by_name = self.profiles_store.get("by_player_name", {})
        self._profiles_by_id = {p["player_id"]: p for p in self.profiles_store.get("profiles", [])}
        self._splits_by_key = self.splits_store.get("by_key", {})
        self._splits_by_name = self.splits_store.get("by_player_name", {})

        # Official Phase 8 indexes
        self._official_batters = self.official_store.get("official_top10_batters", [])
        self._official_bowlers = self.official_store.get("official_top10_bowlers", [])
        self._official_by_name = self.official_store.get("by_player_name", {})
        self._official_by_id = self.official_store.get("by_player_id", {})

        # Build cohort index for peer comparisons
        self._cohort_players: Dict[str, List[Dict[str, Any]]] = {}
        for p in self.profiles_store.get("profiles", []):
            cohort = p["cohort"]
            if cohort not in self._cohort_players:
                self._cohort_players[cohort] = []
            self._cohort_players[cohort].append(p)

    def get_official_rankings(self, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns the authoritative Phase 8 Unified Official Rankings with 90% rank CIs.
        """
        role_norm = role.strip().capitalize() if role else None
        batters = self.official_store.get("official_top10_batters", [])
        bowlers = self.official_store.get("official_top10_bowlers", [])
        cand_batters = self.official_store.get("candidate_batters", [])
        cand_bowlers = self.official_store.get("candidate_bowlers", [])

        if role_norm == "Batter":
            return {
                "role": "Batter",
                "title": "Official Top 10 Batters (SupeRR Selector Season 2)",
                "total_official": len(batters),
                "total_candidates": len(batters) + len(cand_batters),
                "official_top10": batters,
                "candidates": cand_batters,
                "metadata": self.official_store.get("metadata", {})
            }
        elif role_norm == "Bowler":
            return {
                "role": "Bowler",
                "title": "Official Top 10 Bowlers (SupeRR Selector Season 2)",
                "total_official": len(bowlers),
                "total_candidates": len(bowlers) + len(cand_bowlers),
                "official_top10": bowlers,
                "candidates": cand_bowlers,
                "metadata": self.official_store.get("metadata", {})
            }
        else:
            return {
                "version": self.official_store.get("version", "CPRI-v1.0.0-PHASE8-OFFICIAL"),
                "title": "SupeRR Intelligence — Official Competition Rankings",
                "batters": batters,
                "bowlers": bowlers,
                "metadata": self.official_store.get("metadata", {})
            }

    def get_official_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns unified official player record by name (case-insensitive).
        """
        name_clean = player_name.strip().lower()
        for name, p in self._official_by_name.items():
            if name.lower() == name_clean:
                return p
        return None

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Scouting data store not found at {filepath}. Run python scripts/build_official_store.py or python scripts/build_scouting_store.py first.")
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # -------------------------------------------------------------------------
    # Feature 1: Get Player Profile
    # -------------------------------------------------------------------------
    def get_player_profile(
        self,
        player_name: Optional[str] = None,
        player_id: Optional[int] = None,
        competition_scope: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a player's scouting profile by name or numeric ID,
        with optional scope ('IPL', 'T20I') and role ('Batter', 'Bowler') filtering.
        """
        scope_upper = competition_scope.strip().upper() if competition_scope else None
        role_title = role.strip().capitalize() if role else None

        if player_id is not None:
            # Match by ID
            matches = [
                p for p in self.profiles_store.get("profiles", [])
                if p["player_id"] == player_id
                and (scope_upper is None or p["competition_scope"].upper() == scope_upper)
                and (role_title is None or p["role"].capitalize() == role_title)
            ]
            if matches:
                return matches[0]
            return None

        if player_name is not None:
            name_clean = player_name.strip()
            # Fast index match
            if name_clean in self._profiles_by_name:
                scope_dict = self._profiles_by_name[name_clean]
                if scope_upper is not None:
                    profile = scope_dict.get(scope_upper)
                    if profile and (role_title is None or profile["role"].capitalize() == role_title):
                        return profile
                else:
                    for s, prof in scope_dict.items():
                        if role_title is None or prof["role"].capitalize() == role_title:
                            return prof

            # Case-insensitive search fallback
            name_lower = name_clean.lower()
            for p in self.profiles_store.get("profiles", []):
                if p["player_name"].lower() == name_lower:
                    if (scope_upper is None or p["competition_scope"].upper() == scope_upper) and \
                       (role_title is None or p["role"].capitalize() == role_title):
                        return p

        return None

    # -------------------------------------------------------------------------
    # Feature 2: Get Contextual Performance Splits
    # -------------------------------------------------------------------------
    def get_contextual_splits(
        self,
        player_name: Optional[str] = None,
        player_id: Optional[int] = None,
        competition_scope: Optional[str] = None,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves contextual performance splits:
        - Powerplay, Middle, Death overs
        - Against Pace vs Spin (for Batters)
        - Against RHB vs LHB (for Bowlers)
        - Pressure vs Non-Pressure contrasts
        """
        profile = self.get_player_profile(player_name, player_id, competition_scope, role)
        if not profile:
            return None

        key = profile["profile_key"]
        return self._splits_by_key.get(key)

    @property
    def h2h_store(self) -> Dict[str, Any]:
        """Lazy-loads head_to_head_matrix.json to conserve RAM and startup time."""
        if self._h2h_store is None:
            self._h2h_store = self._load_json("head_to_head_matrix.json")
            self._h2h_by_key = self._h2h_store.get("by_key", {})
        return self._h2h_store

    @property
    def h2h_by_key(self) -> Dict[str, Any]:
        if self._h2h_by_key is None:
            _ = self.h2h_store
        return self._h2h_by_key

    # -------------------------------------------------------------------------
    # Feature 3: Get Batter-versus-Bowler Matchup
    # -------------------------------------------------------------------------
    def get_head_to_head(
        self,
        batter_name: str,
        bowler_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """
        Retrieves head-to-head record between batter and bowler in a specific format.
        Preserves strict format separation and assigns explicit sample tier.
        """
        b_name = batter_name.strip()
        bw_name = bowler_name.strip()
        scope = competition_scope.strip().upper()

        by_key = self.h2h_by_key
        key = f"{b_name} vs {bw_name} [{scope}]"
        if key in by_key:
            return by_key[key]

        # Case-insensitive lookup
        key_lower = key.lower()
        for k, v in by_key.items():
            if k.lower() == key_lower:
                return v

        # Return structured zero-sample record if no encounter has occurred
        return {
            "matchup_id": f"{scope}_UNKNOWN",
            "matchup_key": key,
            "competition_scope": scope,
            "batter_id": None,
            "batter_name": b_name,
            "bowler_id": None,
            "bowler_name": bw_name,
            "balls_faced": 0,
            "runs_scored": 0,
            "dismissals": 0,
            "fours": 0,
            "sixes": 0,
            "dot_balls": 0,
            "strike_rate": 0.0,
            "batting_average": None,
            "balls_per_dismissal": None,
            "dot_percentage": 0.0,
            "boundary_percentage": 0.0,
            "avg_pressure_score": None,
            "sample_tier": "No Historical Encounters (0 balls)",
            "is_statistically_reliable": False,
            "ranked_player_involved": False,
            "notes": "No recorded deliveries between this batter and bowler in the selected competition scope."
        }

    # -------------------------------------------------------------------------
    # Feature 4: Compare Two Batters
    # -------------------------------------------------------------------------
    def compare_batters(
        self,
        batter_a: str,
        batter_b: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """
        Conducts a role-adjusted comparison between two batters in the same format.
        Compares CPRI scores, components, situational splits, and pressure deltas.
        """
        prof_a = self.get_player_profile(batter_a, competition_scope=competition_scope, role="Batter")
        prof_b = self.get_player_profile(batter_b, competition_scope=competition_scope, role="Batter")

        if not prof_a:
            raise ValueError(f"Batter '{batter_a}' not found in {competition_scope} Batter profiles.")
        if not prof_b:
            raise ValueError(f"Batter '{batter_b}' not found in {competition_scope} Batter profiles.")

        splits_a = self.get_contextual_splits(batter_a, competition_scope=competition_scope, role="Batter")
        splits_b = self.get_contextual_splits(batter_b, competition_scope=competition_scope, role="Batter")

        comp_a = prof_a["components"]
        comp_b = prof_b["components"]

        # Component deltas (A minus B)
        deltas = {
            "cpri_delta": round(prof_a["cpri_score"] - prof_b["cpri_score"], 2),
            "pressure_impact_delta": round(comp_a["pressure_impact"] - comp_b["pressure_impact"], 2),
            "adaptability_delta": round(comp_a["pressure_adaptability"] - comp_b["pressure_adaptability"], 2),
            "consistency_delta": round(comp_a["clutch_consistency"] - comp_b["clutch_consistency"], 2),
            "reliability_delta": round(comp_a["reliability_confidence"] - comp_b["reliability_confidence"], 2)
        }

        # Situational comparison
        phase_comp = {}
        for phase in ["powerplay", "middle", "death"]:
            p_a = splits_a["innings_phase_splits"][phase] if splits_a else {}
            p_b = splits_b["innings_phase_splits"][phase] if splits_b else {}
            phase_comp[phase] = {
                f"{batter_a}_sr": p_a.get("strike_rate"),
                f"{batter_b}_sr": p_b.get("strike_rate"),
                f"{batter_a}_balls": p_a.get("balls_faced"),
                f"{batter_b}_balls": p_b.get("balls_faced"),
                "higher_strike_rate_player": batter_a if (p_a.get("strike_rate", 0) or 0) >= (p_b.get("strike_rate", 0) or 0) else batter_b
            }

        return {
            "comparison_scope": competition_scope,
            "batter_a": {
                "name": prof_a["player_name"],
                "official_rank": prof_a["official_rank"],
                "ranking_tier": prof_a["ranking_tier"],
                "cpri_score": prof_a["cpri_score"],
                "components": comp_a,
                "overall_strike_rate": prof_a["performance_stats"].get("strike_rate"),
                "pressure_strike_rate": prof_a["performance_stats"]["pressure_stats"].get("pressure_strike_rate"),
                "pressure_classification": splits_a["pressure_contrast"]["tactical_classification"] if splits_a else "Unknown"
            },
            "batter_b": {
                "name": prof_b["player_name"],
                "official_rank": prof_b["official_rank"],
                "ranking_tier": prof_b["ranking_tier"],
                "cpri_score": prof_b["cpri_score"],
                "components": comp_b,
                "overall_strike_rate": prof_b["performance_stats"].get("strike_rate"),
                "pressure_strike_rate": prof_b["performance_stats"]["pressure_stats"].get("pressure_strike_rate"),
                "pressure_classification": splits_b["pressure_contrast"]["tactical_classification"] if splits_b else "Unknown"
            },
            "deltas_a_minus_b": deltas,
            "phase_comparison": phase_comp
        }

    # -------------------------------------------------------------------------
    # Feature 5: Retrieve Player's Pressure Statistics
    # -------------------------------------------------------------------------
    def get_pressure_stats(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves detailed high-pressure (PI >= 50) and low-pressure (PI < 50) statistics,
        including frozen sample sizes, WPA contributions, and tactical classifications.
        """
        profile = self.get_player_profile(player_name, competition_scope=competition_scope, role=role)
        if not profile:
            raise ValueError(f"Player '{player_name}' not found in {competition_scope}.")

        splits = self.get_contextual_splits(player_name, competition_scope=competition_scope, role=role)
        contrast = splits.get("pressure_contrast", {}) if splits else {}

        return {
            "player_name": profile["player_name"],
            "competition_scope": profile["competition_scope"],
            "role": profile["role"],
            "cpri_score": profile["cpri_score"],
            "official_rank": profile["official_rank"],
            "ranking_tier": profile["ranking_tier"],
            "confidence_tier": profile["confidence_tier"],
            "frozen_pressure_deliveries": profile["exposure"]["pressure_deliveries"],
            "frozen_pressure_matches": profile["exposure"]["pressure_matches"],
            "pos_pressure_match_ratio": profile["exposure"]["pos_pressure_match_ratio"],
            "pressure_contrast": contrast,
            "performance_stats_pressure": profile["performance_stats"].get("pressure_stats", {}),
            "performance_stats_nonpressure": profile["performance_stats"].get("nonpressure_stats", {}),
            "tactical_classification": contrast.get("tactical_classification", "Unclassified")
        }

    # -------------------------------------------------------------------------
    # Feature 6: Retrieve Strengths and Weaknesses
    # -------------------------------------------------------------------------
    def get_strengths_and_weaknesses(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts evidence-backed strengths and vulnerabilities strictly from empirical metrics.
        Never fabricates unrecorded metrics.
        """
        profile = self.get_player_profile(player_name, competition_scope=competition_scope, role=role)
        if not profile:
            raise ValueError(f"Player '{player_name}' not found in {competition_scope}.")

        splits = self.get_contextual_splits(player_name, competition_scope=competition_scope, role=role)
        strengths = []
        weaknesses = []
        neutral_observations = []

        is_batter = profile["role"] == "Batter"

        if is_batter and splits:
            phases = splits["innings_phase_splits"]
            bowling_type = splits["bowling_type_splits"]
            contrast = splits["pressure_contrast"]
            p_stats = profile["performance_stats"]

            # 1. Death overs prowess
            death = phases.get("death", {})
            if death.get("balls_faced", 0) >= 30:
                sr = death.get("strike_rate", 0)
                if sr >= 175.0:
                    strengths.append(f"Elite Death Overs Finisher: Strike rate of {sr:.1f} across {death['balls_faced']} balls in overs 17-20.")
                elif sr < 140.0:
                    weaknesses.append(f"Sub-par Death Overs Acceleration: Strike rate of {sr:.1f} in death overs.")

            # 2. Bowling type matchup (Pace vs Spin)
            pace = bowling_type.get("pace", {})
            spin = bowling_type.get("spin", {})
            if pace.get("balls_faced", 0) >= 30 and spin.get("balls_faced", 0) >= 30:
                pace_sr = pace.get("strike_rate", 0)
                spin_sr = spin.get("strike_rate", 0)
                delta_bowling = pace_sr - spin_sr
                if delta_bowling >= 20.0:
                    strengths.append(f"Dominant Pace Striking: Scores at {pace_sr:.1f} SR vs Pace compared to {spin_sr:.1f} SR vs Spin (+{delta_bowling:.1f} delta).")
                    weaknesses.append(f"Vulnerability to Spin: Strike rate drops to {spin_sr:.1f} against spin bowlers.")
                elif delta_bowling <= -20.0:
                    strengths.append(f"Exceptional Spin Tactician: Scores at {spin_sr:.1f} SR vs Spin compared to {pace_sr:.1f} SR vs Pace.")
                    weaknesses.append(f"Pace Vulnerability: Strike rate falls to {pace_sr:.1f} vs Pace bowling.")
                else:
                    neutral_observations.append(f"Balanced Matchup Profile: Consistent scoring against Pace ({pace_sr:.1f} SR) and Spin ({spin_sr:.1f} SR).")

            # 3. Pressure Contrast
            delta_sr = contrast.get("delta_strike_rate", 0)
            if delta_sr >= 10.0:
                strengths.append(f"Clutch Acceleration: Strike rate increases by +{delta_sr:.1f} under high pressure (PI >= 50) vs low pressure.")
            elif delta_sr <= -10.0:
                weaknesses.append(f"Pressure Degradation: Strike rate drops by {delta_sr:.1f} points under high game pressure.")

            # 4. Dot ball avoidance
            dot_pct = p_stats.get("dot_percentage", 0)
            if dot_pct <= 28.0:
                strengths.append(f"Outstanding Strike Rotation: Low career dot ball rate of {dot_pct:.1f}%.")
            elif dot_pct >= 40.0:
                weaknesses.append(f"High Dot Ball Accumulation: Consumes {dot_pct:.1f}% dot balls.")

        elif not is_batter and splits:
            # Bowler strengths and weaknesses
            phases = splits["innings_phase_splits"]
            hand = splits["batter_hand_splits"]
            contrast = splits["pressure_contrast"]
            p_stats = profile["performance_stats"]

            # 1. Death overs economy & wicket threat
            death = phases.get("death", {})
            if death.get("balls_bowled", 0) >= 30:
                econ = death.get("economy_rate", 0)
                wkts = death.get("credited_wickets", 0)
                if econ <= 8.5:
                    strengths.append(f"Elite Death Overs Restriction: Concedes just {econ:.2f} runs/over across {death['balls_bowled']} death balls with {wkts} wickets.")
                elif econ >= 10.5:
                    weaknesses.append(f"Vulnerable at the Death: Concedes {econ:.2f} runs/over in overs 17-20.")

            # 2. Powerplay control
            pp = phases.get("powerplay", {})
            if pp.get("balls_bowled", 0) >= 30:
                pp_econ = pp.get("economy_rate", 0)
                if pp_econ <= 6.8:
                    strengths.append(f"Powerplay Enforcer: Outstanding opening economy of {pp_econ:.2f} across {pp['balls_bowled']} balls.")

            # 3. Handedness bias
            rhb = hand.get("rhb", {})
            lhb = hand.get("lhb", {})
            if rhb.get("balls_bowled", 0) >= 30 and lhb.get("balls_bowled", 0) >= 30:
                rhb_econ = rhb.get("economy_rate", 0)
                lhb_econ = lhb.get("economy_rate", 0)
                delta_hand = lhb_econ - rhb_econ
                if delta_hand >= 1.5:
                    weaknesses.append(f"Left-Hand Batter Vulnerability: Economy expands to {lhb_econ:.2f} vs LHB vs {rhb_econ:.2f} vs RHB (+{delta_hand:.2f} delta).")
                elif delta_hand <= -1.5:
                    strengths.append(f"LHB Neutralizer: Concedes only {lhb_econ:.2f} against Left-Hand Batters.")

            # 4. Dot ball dominance
            dot_pct = p_stats.get("dot_percentage", 0)
            if dot_pct >= 42.0:
                strengths.append(f"High Dot Ball Frequency: Forces dots on {dot_pct:.1f}% of legal deliveries.")

        return {
            "player_name": profile["player_name"],
            "competition_scope": profile["competition_scope"],
            "role": profile["role"],
            "cpri_score": profile["cpri_score"],
            "strengths": strengths if strengths else ["Solid baseline execution across evaluated metrics."],
            "weaknesses": weaknesses if weaknesses else ["No severe systemic weaknesses detected under current sample thresholds."],
            "neutral_observations": neutral_observations
        }

    # -------------------------------------------------------------------------
    # Feature 7: Retrieve Peer Comparisons within Format and Role
    # -------------------------------------------------------------------------
    def get_peer_comparisons(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes cohort percentile ranks and benchmarking against peers
        within the same format and role.
        """
        profile = self.get_player_profile(player_name, competition_scope=competition_scope, role=role)
        if not profile:
            raise ValueError(f"Player '{player_name}' not found in {competition_scope}.")

        cohort = profile["cohort"]
        peers = self._cohort_players.get(cohort, [])
        if not peers:
            return {"error": f"No peer data available for cohort {cohort}."}

        # Calculate cohort statistics
        cpri_vals = [p["cpri_score"] for p in peers]
        pi_vals = [p["components"]["pressure_impact"] for p in peers]
        pa_vals = [p["components"]["pressure_adaptability"] for p in peers]
        cc_vals = [p["components"]["clutch_consistency"] for p in peers]
        rc_vals = [p["components"]["reliability_confidence"] for p in peers]

        def calc_percentile(val: float, val_list: List[float]) -> float:
            count_below = sum(1 for v in val_list if v < val)
            return round((count_below / max(1, len(val_list))) * 100.0, 1)

        player_cpri = profile["cpri_score"]
        comps = profile["components"]

        # Rank 1 and Top 10 cutoff scores
        sorted_cpri = sorted(cpri_vals, reverse=True)
        rank_1_score = sorted_cpri[0]
        top10_cutoff = sorted_cpri[9] if len(sorted_cpri) >= 10 else sorted_cpri[-1]

        return {
            "player_name": profile["player_name"],
            "cohort": cohort,
            "competition_scope": profile["competition_scope"],
            "role": profile["role"],
            "official_rank": profile["official_rank"],
            "ranking_tier": profile["ranking_tier"],
            "total_cohort_peers": len(peers),
            "player_scores": {
                "cpri_score": player_cpri,
                "pressure_impact": comps["pressure_impact"],
                "pressure_adaptability": comps["pressure_adaptability"],
                "clutch_consistency": comps["clutch_consistency"],
                "reliability_confidence": comps["reliability_confidence"]
            },
            "cohort_percentiles": {
                "cpri_percentile": calc_percentile(player_cpri, cpri_vals),
                "pressure_impact_percentile": calc_percentile(comps["pressure_impact"], pi_vals),
                "adaptability_percentile": calc_percentile(comps["pressure_adaptability"], pa_vals),
                "consistency_percentile": calc_percentile(comps["clutch_consistency"], cc_vals),
                "reliability_percentile": calc_percentile(comps["reliability_confidence"], rc_vals)
            },
            "cohort_benchmarks": {
                "cohort_mean_cpri": round(sum(cpri_vals) / len(cpri_vals), 2),
                "cohort_max_cpri": rank_1_score,
                "top10_cutoff_cpri": top10_cutoff,
                "delta_to_rank_1": round(player_cpri - rank_1_score, 2),
                "delta_to_top10_cutoff": round(player_cpri - top10_cutoff, 2)
            }
        }
