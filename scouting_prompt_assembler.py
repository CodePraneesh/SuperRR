#!/usr/bin/env python3
"""
scouting_prompt_assembler.py
SupeRR Intelligence - Phase 4.3 Grounded Prompt Assembler

Constructs rigorous, anti-hallucination prompt payloads for the 7 core scouting features:
1. AI Player Scouting Reports
2. Pressure Performance Explanations
3. Batter Strengths and Weaknesses
4. Bowler Strengths and Weaknesses
5. Batter vs Batter Comparison
6. Batter vs Bowler Head-to-Head Scouting
7. Natural Language Cricket Analytics

Guarantees:
- Every prompt includes an immutable structured evidence JSON block.
- Explicit sample limitation warnings and confidence tier notices.
- Anti-Hallucination System Directive strictly forbidding extrapolation of ungrounded stats.
"""
import json
from typing import Dict, Any, Optional, List
from scouting_data_engine import ScoutingDataEngine


class ScoutingPromptAssembler:
    """
    Prompt Assembler that builds strictly-grounded prompt payloads
    for language model inference and offline evaluation.
    """

    SYSTEM_GUARDRAIL_DIRECTIVE = (
        "You are SupeRR Intelligence, an elite professional cricket scouting AI.\n"
        "STRICT GROUNDING & ANTI-HALLUCINATION RULES:\n"
        "1. GROUND TRUTH IMMUTABILITY: You must ONLY cite exact numbers, ranks, and metrics provided "
        "in the verified EVIDENCE BLOCK below. Never invent, extrapolate, or guess any cricket statistics.\n"
        "2. UNRECORDED METRICS: Trajectory, continuous ball release speed, and unrecorded metrics do not exist in the dataset; "
        "do not invent them.\n"
        "3. MISSING SAMPLES: If a metric is null or sample size is zero (e.g. 0 balls faced in powerplay), state clearly that "
        "there is no sample rather than claiming poor performance.\n"
        "4. SAMPLE LIMITATIONS: Always mention the sample tier and limitation warning when citing low-sample splits or head-to-head records.\n"
        "5. SEPARATION OF OPINION AND FACT: Clearly distinguish verified historical performance statistics from tactical scouting assessments."
    )

    def __init__(self, engine: Optional[ScoutingDataEngine] = None):
        self.engine = engine if engine is not None else ScoutingDataEngine()

    def _assemble_payload(
        self,
        feature_name: str,
        user_prompt: str,
        evidence: Dict[str, Any],
        limitations: List[str]
    ) -> Dict[str, Any]:
        """Utility to pack and serialize structured prompt payload."""
        limitations_block = "\n".join(f"- WARNING: {lim}" for lim in limitations) if limitations else "No critical sample limitations detected."

        formatted_prompt = (
            f"=== SYSTEM DIRECTIVE ===\n"
            f"{self.SYSTEM_GUARDRAIL_DIRECTIVE}\n\n"
            f"=== VERIFIED STATISTICAL EVIDENCE (IMMUTABLE GROUND TRUTH) ===\n"
            f"```json\n{json.dumps(evidence, indent=2)}\n```\n\n"
            f"=== SAMPLE LIMITATIONS & RELIABILITY WARNINGS ===\n"
            f"{limitations_block}\n\n"
            f"=== USER SCOUTING TASK ===\n"
            f"{user_prompt}\n\n"
            f"Provide your professional scouting response strictly adhering to the verified statistical evidence above."
        )

        return {
            "feature": feature_name,
            "system_prompt": self.SYSTEM_GUARDRAIL_DIRECTIVE,
            "user_prompt": user_prompt,
            "evidence_payload": evidence,
            "sample_limitations": limitations,
            "assembled_prompt": formatted_prompt
        }

    # -------------------------------------------------------------------------
    # Feature 1: AI Player Scouting Report Prompt
    # -------------------------------------------------------------------------
    def build_scouting_report_prompt(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds a grounded prompt for a comprehensive player scouting report."""
        profile = self.engine.get_player_profile(player_name, competition_scope=competition_scope, role=role)
        if not profile:
            raise ValueError(f"Player '{player_name}' not found in {competition_scope}.")

        splits = self.engine.get_contextual_splits(player_name, competition_scope=competition_scope, role=role)
        peers = self.engine.get_peer_comparisons(player_name, competition_scope=competition_scope, role=role)
        sw = self.engine.get_strengths_and_weaknesses(player_name, competition_scope=competition_scope, role=role)

        evidence = {
            "profile": profile,
            "contextual_splits": splits,
            "peer_benchmarks": peers,
            "empirical_strengths_and_weaknesses": sw
        }

        limitations = []
        if profile.get("is_provisional_top5"):
            limitations.append(f"Player holds PROVISIONAL ranking status due to sub-threshold pressure sample ({profile['exposure']['pressure_deliveries']} balls).")
        if profile["confidence_tier"] != "High Confidence":
            limitations.append(f"Confidence tier is '{profile['confidence_tier']}'; uncertainty intervals are wide.")

        user_prompt = (
            f"Generate a comprehensive, executive-ready Scouting Intelligence Report for {profile['player_name']} "
            f"in {profile['competition_scope']} ({profile['role']}). "
            f"Synthesize their CPRI standing ({profile['cpri_score']} - Rank {profile['official_rank']}), "
            f"phase-by-phase execution, pressure adaptation, peer percentiles, and tactical match role."
        )

        return self._assemble_payload("player_scouting_report", user_prompt, evidence, limitations)

    # -------------------------------------------------------------------------
    # Feature 2: Pressure Performance Explanation Prompt
    # -------------------------------------------------------------------------
    def build_pressure_explanation_prompt(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Builds a grounded prompt analyzing why a player excels or struggles under pressure."""
        p_stats = self.engine.get_pressure_stats(player_name, competition_scope=competition_scope, role=role)
        profile = self.engine.get_player_profile(player_name, competition_scope=competition_scope, role=role)

        evidence = {
            "pressure_analysis": p_stats,
            "frozen_cpri_components": profile["components"] if profile else {},
            "bootstrap_uncertainty": profile.get("bootstrap_uncertainty", {}) if profile else {}
        }

        limitations = []
        p_delivs = p_stats["frozen_pressure_deliveries"]
        if p_delivs < 100:
            limitations.append(f"Pressure sample of {p_delivs} deliveries is below the 100-ball full statistical threshold.")

        user_prompt = (
            f"Explain the pressure performance profile of {player_name} in {competition_scope}. "
            f"Focus on how their performance shifts when Pressure Index (PI) exceeds 50.0. "
            f"Detail their Pressure Impact ({profile['components']['pressure_impact']:.1f}), "
            f"Adaptability ({profile['components']['pressure_adaptability']:.1f}), "
            f"Consistency ({profile['components']['clutch_consistency']:.1f}), and tactical classification '{p_stats['tactical_classification']}'."
        )

        return self._assemble_payload("pressure_performance_explanation", user_prompt, evidence, limitations)

    # -------------------------------------------------------------------------
    # Feature 3: Batter Strengths and Weaknesses Prompt
    # -------------------------------------------------------------------------
    def build_batter_strengths_weaknesses_prompt(
        self,
        player_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Builds a grounded prompt detailing batter tactical strengths and weaknesses."""
        profile = self.engine.get_player_profile(player_name, competition_scope=competition_scope, role="Batter")
        if not profile:
            raise ValueError(f"Batter '{player_name}' not found in {competition_scope}.")

        splits = self.engine.get_contextual_splits(player_name, competition_scope=competition_scope, role="Batter")
        sw = self.engine.get_strengths_and_weaknesses(player_name, competition_scope=competition_scope, role="Batter")

        evidence = {
            "player_name": profile["player_name"],
            "competition_scope": profile["competition_scope"],
            "innings_phase_splits": splits.get("innings_phase_splits", {}) if splits else {},
            "bowling_type_splits": splits.get("bowling_type_splits", {}) if splits else {},
            "pressure_contrast": splits.get("pressure_contrast", {}) if splits else {},
            "strengths_evidence": sw["strengths"],
            "weaknesses_evidence": sw["weaknesses"]
        }

        limitations = []
        if splits:
            for phase_k, phase_v in splits.get("innings_phase_splits", {}).items():
                if phase_v.get("balls_faced", 0) < 15:
                    limitations.append(f"{phase_k.capitalize()} sample is low ({phase_v.get('balls_faced', 0)} balls faced).")

        user_prompt = (
            f"Provide an evidence-based Strengths and Vulnerabilities Dossier for batter {player_name} in {competition_scope}. "
            f"Break down their phase-specific strike rates, performance against Pace vs Spin, and reaction to game pressure. "
            f"Cite exact strike rates, boundary percentages, and dot-ball ratios from the evidence."
        )

        return self._assemble_payload("batter_strengths_weaknesses", user_prompt, evidence, limitations)

    # -------------------------------------------------------------------------
    # Feature 4: Bowler Strengths and Weaknesses Prompt
    # -------------------------------------------------------------------------
    def build_bowler_strengths_weaknesses_prompt(
        self,
        player_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Builds a grounded prompt detailing bowler tactical strengths and weaknesses."""
        profile = self.engine.get_player_profile(player_name, competition_scope=competition_scope, role="Bowler")
        if not profile:
            raise ValueError(f"Bowler '{player_name}' not found in {competition_scope}.")

        splits = self.engine.get_contextual_splits(player_name, competition_scope=competition_scope, role="Bowler")
        sw = self.engine.get_strengths_and_weaknesses(player_name, competition_scope=competition_scope, role="Bowler")

        evidence = {
            "player_name": profile["player_name"],
            "competition_scope": profile["competition_scope"],
            "innings_phase_splits": splits.get("innings_phase_splits", {}) if splits else {},
            "batter_hand_splits": splits.get("batter_hand_splits", {}) if splits else {},
            "pressure_contrast": splits.get("pressure_contrast", {}) if splits else {},
            "strengths_evidence": sw["strengths"],
            "weaknesses_evidence": sw["weaknesses"]
        }

        limitations = []
        if splits:
            for phase_k, phase_v in splits.get("innings_phase_splits", {}).items():
                if phase_v.get("balls_bowled", 0) < 12:
                    limitations.append(f"{phase_k.capitalize()} sample is low ({phase_v.get('balls_bowled', 0)} balls bowled).")

        user_prompt = (
            f"Provide an evidence-based Strengths and Vulnerabilities Dossier for bowler {player_name} in {competition_scope}. "
            f"Analyze their phase deployment (Powerplay vs Middle vs Death), run containment vs RHB and LHB batters, "
            f"and high-pressure economy rate."
        )

        return self._assemble_payload("bowler_strengths_weaknesses", user_prompt, evidence, limitations)

    # -------------------------------------------------------------------------
    # Feature 5: Batter vs Batter Comparison Prompt
    # -------------------------------------------------------------------------
    def build_batter_comparison_prompt(
        self,
        batter_a: str,
        batter_b: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Builds a grounded prompt comparing two batters side-by-side."""
        comp = self.engine.compare_batters(batter_a, batter_b, competition_scope=competition_scope)

        limitations = []
        for name in [batter_a, batter_b]:
            p = self.engine.get_player_profile(name, competition_scope=competition_scope, role="Batter")
            if p and p.get("is_provisional_top5"):
                limitations.append(f"{name} has a PROVISIONAL ranking due to small sample size.")

        user_prompt = (
            f"Compare {batter_a} and {batter_b} for a high-leverage tactical batting role in {competition_scope}. "
            f"Break down their CPRI score differential ({comp['deltas_a_minus_b']['cpri_delta']:+.2f}), "
            f"component performance, phase-by-phase scoring efficiency, and suitability for closing out matches."
        )

        return self._assemble_payload("batter_comparison", user_prompt, comp, limitations)

    # -------------------------------------------------------------------------
    # Feature 6: Batter vs Bowler Head-to-Head Scouting Prompt
    # -------------------------------------------------------------------------
    def build_h2h_scouting_prompt(
        self,
        batter_name: str,
        bowler_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Builds a grounded prompt evaluating a specific head-to-head tactical matchup."""
        h2h = self.engine.get_head_to_head(batter_name, bowler_name, competition_scope=competition_scope)
        bat_splits = self.engine.get_contextual_splits(batter_name, competition_scope=competition_scope, role="Batter")
        bowl_splits = self.engine.get_contextual_splits(bowler_name, competition_scope=competition_scope, role="Bowler")

        evidence = {
            "head_to_head_record": h2h,
            "batter_situational_context": bat_splits.get("bowling_type_splits", {}) if bat_splits else {},
            "bowler_situational_context": bowl_splits.get("batter_hand_splits", {}) if bowl_splits else {}
        }

        limitations = []
        if not h2h.get("is_statistically_reliable", False):
            limitations.append(
                f"Head-to-head sample is {h2h.get('sample_tier', 'Low')} ({h2h.get('balls_faced', 0)} balls faced). "
                f"Statistically fragile; tactical conclusions must rely on broader contextual splits."
            )

        user_prompt = (
            f"Evaluate the tactical matchup between batter {batter_name} and bowler {bowler_name} in {competition_scope}. "
            f"Analyze their historical encounter ({h2h.get('balls_faced', 0)} balls, {h2h.get('runs_scored', 0)} runs, {h2h.get('dismissals', 0)} outs), "
            f"strike rate ({h2h.get('strike_rate', 0.0)}), dot-ball percentage ({h2h.get('dot_percentage', 0.0)}%), "
            f"and synthesize a tactical battle plan for both parties."
        )

        return self._assemble_payload("head_to_head_scouting", user_prompt, evidence, limitations)

    # -------------------------------------------------------------------------
    # Feature 7: Natural-Language Cricket Analytics QA Prompt
    # -------------------------------------------------------------------------
    def build_analytics_qa_prompt(
        self,
        query: str,
        entities_involved: Optional[List[str]] = None,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Builds a grounded prompt for general analytical question-answering."""
        evidence: Dict[str, Any] = {
            "query": query,
            "competition_scope": competition_scope,
            "entity_profiles": {}
        }
        limitations = []

        if entities_involved:
            for entity in entities_involved:
                off_prof = self.engine.get_official_player(entity)
                if off_prof:
                    evidence["entity_profiles"][entity] = {
                        "cpri_score": off_prof["cpri_score"],
                        "official_rank": off_prof["official_rank"],
                        "role": off_prof["role"],
                        "ranking_tier": "Official Top 10" if off_prof["is_official_top10"] else "Contender Candidate",
                        "confidence_tier": off_prof["confidence_tier"],
                        "rank_uncertainty": off_prof["rank_uncertainty"],
                        "components": off_prof["components"],
                        "exposure": off_prof["pressure_stats"]
                    }
                else:
                    prof = self.engine.get_player_profile(entity, competition_scope=competition_scope)
                    if prof:
                        evidence["entity_profiles"][entity] = {
                            "cpri_score": prof["cpri_score"],
                            "official_rank": prof["official_rank"],
                            "ranking_tier": prof["ranking_tier"],
                            "components": prof["components"],
                            "exposure": prof["exposure"]
                        }
                    else:
                        evidence["entity_profiles"][entity] = {"status": "Player not found in ranked stores"}

        user_prompt = (
            f"Answer the following cricket analytics query: \"{query}\". "
            f"Rely strictly on the verified data in the evidence payload. "
            f"Do not introduce outside speculative assertions."
        )

        return self._assemble_payload("natural_language_analytics", user_prompt, evidence, limitations)
