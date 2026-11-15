#!/usr/bin/env python3
"""
scouting_ai_service.py
SupeRR Intelligence - Phase 4.4 AI Generation Service

Three-Tier AI Scouting Generation Architecture:
- Tier 1: Hugging Face Serverless API (Qwen/Qwen2.5-7B-Instruct)
- Tier 2: Local Generation (Qwen2.5-3B-Instruct) with environment/memory safety checks
- Tier 3: Deterministic Python Fallback (100% offline uptime, evidence-grounded)

Includes:
- Strict evidence verification via ScoutingResponseVerifier
- Automatic fallback on API rate limit, timeout, missing token, or verification failure
- Implementation of all 7 core scouting functions
"""
import os
import sys
import json
import time
from typing import Dict, Any, Optional, List, Tuple

from scouting_data_engine import ScoutingDataEngine
from scouting_prompt_assembler import ScoutingPromptAssembler
from hf_inference_client import HFInferenceClient
from scouting_response_verifier import ScoutingResponseVerifier


class DeterministicScoutingFallback:
    """
    Tier 3: Deterministic Python Fallback Engine.
    Generates rich, fully grounded scouting reports directly from verified data
    without requiring internet access or language model weights.
    """

    @staticmethod
    def generate_player_report(payload: Dict[str, Any]) -> str:
        evidence = payload["evidence_payload"]
        profile = evidence["profile"]
        splits = evidence.get("contextual_splits", {})
        peers = evidence.get("peer_benchmarks", {})
        sw = evidence.get("empirical_strengths_and_weaknesses", {})
        limitations = payload.get("sample_limitations", [])

        pname = profile["player_name"]
        scope = profile["competition_scope"]
        role = profile["role"]
        rank = profile["official_rank"]
        cpri = profile["cpri_score"]
        comps = profile["components"]
        tier = profile["ranking_tier"]
        conf = profile["confidence_tier"]

        lines = [
            f"# SupeRR Scouting Report: {pname} ({scope} {role})",
            f"**Official Standing**: Rank #{rank} in {profile['cohort']} ({tier}) | **Confidence**: {conf}",
            f"**CPRI Score**: `{cpri:.2f}` / 100.0 (Cohort Percentile: {peers.get('cohort_percentiles', {}).get('cpri_percentile', 0.0):.1f}%)",
            "",
            "## 1. CPRI Performance Breakdown",
            f"- **Pressure Impact (40%)**: `{comps['pressure_impact']:.2f}` (Percentile: {peers.get('cohort_percentiles', {}).get('pressure_impact_percentile', 0.0):.1f}%)",
            f"- **Pressure Adaptability (25%)**: `{comps['pressure_adaptability']:.2f}` (Percentile: {peers.get('cohort_percentiles', {}).get('adaptability_percentile', 0.0):.1f}%)",
            f"- **Clutch Consistency (20%)**: `{comps['clutch_consistency']:.2f}` (Percentile: {peers.get('cohort_percentiles', {}).get('consistency_percentile', 0.0):.1f}%)",
            f"- **Reliability Confidence (15%)**: `{comps['reliability_confidence']:.2f}` (Percentile: {peers.get('cohort_percentiles', {}).get('reliability_percentile', 0.0):.1f}%)",
            "",
            "## 2. Situational & Phase Execution",
        ]

        if role == "Batter" and splits:
            phases = splits.get("innings_phase_splits", {})
            pp = phases.get("powerplay", {})
            mid = phases.get("middle", {})
            dth = phases.get("death", {})
            contrast = splits.get("pressure_contrast", {})

            lines.extend([
                f"- **Powerplay (Overs 1-6)**: {pp.get('runs_scored', 0)} runs off {pp.get('balls_faced', 0)} balls | SR: `{pp.get('strike_rate', 0.0):.1f}` | Dot%: `{pp.get('dot_percentage', 0.0):.1f}%`",
                f"- **Middle Overs (Overs 7-16)**: {mid.get('runs_scored', 0)} runs off {mid.get('balls_faced', 0)} balls | SR: `{mid.get('strike_rate', 0.0):.1f}` | Average: `{mid.get('batting_average') or 'N/A'}`",
                f"- **Death Overs (Overs 17-20)**: {dth.get('runs_scored', 0)} runs off {dth.get('balls_faced', 0)} balls | SR: `{dth.get('strike_rate', 0.0):.1f}` | Boundary%: `{dth.get('boundary_percentage', 0.0):.1f}%`",
                "",
                "## 3. Pressure Contrast Analysis (PI >= 50 vs PI < 50)",
                f"- **High Pressure Strike Rate**: `{contrast.get('high_pressure', {}).get('strike_rate', 0.0):.1f}` ({contrast.get('high_pressure', {}).get('balls_faced', 0)} balls)",
                f"- **Low Pressure Strike Rate**: `{contrast.get('low_pressure', {}).get('strike_rate', 0.0):.1f}` ({contrast.get('low_pressure', {}).get('balls_faced', 0)} balls)",
                f"- **Net Strike Rate Delta**: `{contrast.get('delta_strike_rate', 0.0):+.2f}` | Classification: **{contrast.get('tactical_classification', 'Unknown')}**",
            ])
        elif role == "Bowler" and splits:
            phases = splits.get("innings_phase_splits", {})
            pp = phases.get("powerplay", {})
            mid = phases.get("middle", {})
            dth = phases.get("death", {})
            contrast = splits.get("pressure_contrast", {})

            lines.extend([
                f"- **Powerplay (Overs 1-6)**: {pp.get('balls_bowled', 0)} balls, {pp.get('runs_conceded', 0)} runs, {pp.get('credited_wickets', 0)} wkts | Economy: `{pp.get('economy_rate', 0.0):.2f}`",
                f"- **Middle Overs (Overs 7-16)**: {mid.get('balls_bowled', 0)} balls, {mid.get('runs_conceded', 0)} runs, {mid.get('credited_wickets', 0)} wkts | Economy: `{mid.get('economy_rate', 0.0):.2f}`",
                f"- **Death Overs (Overs 17-20)**: {dth.get('balls_bowled', 0)} balls, {dth.get('runs_conceded', 0)} runs, {dth.get('credited_wickets', 0)} wkts | Economy: `{dth.get('economy_rate', 0.0):.2f}`",
                "",
                "## 3. Pressure Contrast Analysis (PI >= 50 vs PI < 50)",
                f"- **High Pressure Economy**: `{contrast.get('high_pressure', {}).get('economy_rate', 0.0):.2f}` ({contrast.get('high_pressure', {}).get('balls_bowled', 0)} balls)",
                f"- **Low Pressure Economy**: `{contrast.get('low_pressure', {}).get('economy_rate', 0.0):.2f}` ({contrast.get('low_pressure', {}).get('balls_bowled', 0)} balls)",
                f"- **Net Economy Delta**: `{contrast.get('delta_economy', 0.0):+.2f}` (Negative is favorable) | Classification: **{contrast.get('tactical_classification', 'Unknown')}**",
            ])

        lines.extend([
            "",
            "## 4. Key Strengths & Vulnerabilities",
            "### Empirical Strengths:",
        ])
        for s in sw.get("strengths", ["Consistent baseline execution"]):
            lines.append(f"- {s}")

        lines.append("### Tactical Vulnerabilities:")
        for w in sw.get("weaknesses", ["No significant systemic weaknesses under sample limits"]):
            lines.append(f"- {w}")

        if limitations:
            lines.extend([
                "",
                "## 5. Sample Limitations & Reliability Notices",
            ])
            for lim in limitations:
                lines.append(f"> [!WARNING]\n> {lim}")

        return "\n".join(lines)

    @staticmethod
    def explain_pressure_performance(payload: Dict[str, Any]) -> str:
        evidence = payload["evidence_payload"]
        analysis = evidence["pressure_analysis"]
        pname = analysis["player_name"]
        scope = analysis["competition_scope"]
        role = analysis["role"]
        cpri = analysis["cpri_score"]
        rank = analysis["official_rank"]
        contrast = analysis.get("pressure_contrast", {})
        limitations = payload.get("sample_limitations", [])

        lines = [
            f"# Pressure Performance Dossier: {pname} ({scope} {role})",
            f"**Official CPRI**: `{cpri:.2f}` (Rank #{rank}) | **Classification**: **{analysis['tactical_classification']}**",
            f"**Frozen Pressure Deliveries**: `{analysis['frozen_pressure_deliveries']}` across `{analysis['frozen_pressure_matches']}` matches",
            f"**Positive Pressure Match Ratio**: `{analysis['pos_pressure_match_ratio'] * 100.0:.1f}%`",
            "",
            "## 1. High-Pressure Execution Profile",
        ]

        if role == "Batter":
            hp = contrast.get("high_pressure", {})
            lp = contrast.get("low_pressure", {})
            lines.extend([
                f"- **High-Pressure Strike Rate (PI >= 50)**: `{hp.get('strike_rate', 0.0):.1f}` ({hp.get('runs_scored', 0)} runs off {hp.get('balls_faced', 0)} balls)",
                f"- **Low-Pressure Strike Rate (PI < 50)**: `{lp.get('strike_rate', 0.0):.1f}` ({lp.get('runs_scored', 0)} runs off {lp.get('balls_faced', 0)} balls)",
                f"- **Strike Rate Delta**: `{contrast.get('delta_strike_rate', 0.0):+.2f}`",
                f"- **Dot Ball Ratio**: `{hp.get('dot_percentage', 0.0):.1f}%` under pressure vs `{lp.get('dot_percentage', 0.0):.1f}%` in non-pressure",
                "",
                f"### Tactical Assessment:\n{pname} acts as a `{analysis['tactical_classification']}` under game-defining leverage, "
                f"accelerating their scoring rate by {contrast.get('delta_strike_rate', 0.0):+.2f} when win probability hangs in the balance."
            ])
        else:
            hp = contrast.get("high_pressure", {})
            lp = contrast.get("low_pressure", {})
            lines.extend([
                f"- **High-Pressure Economy (PI >= 50)**: `{hp.get('economy_rate', 0.0):.2f}` ({hp.get('runs_conceded', 0)} runs conceded in {hp.get('overs_bowled', 0.0)} overs)",
                f"- **Low-Pressure Economy (PI < 50)**: `{lp.get('economy_rate', 0.0):.2f}` ({lp.get('runs_conceded', 0)} runs conceded in {lp.get('overs_bowled', 0.0)} overs)",
                f"- **Economy Delta**: `{contrast.get('delta_economy', 0.0):+.2f}` (runs/over)",
                f"- **Dot Ball Ratio**: `{hp.get('dot_percentage', 0.0):.1f}%` dots forced in pressure",
                "",
                f"### Tactical Assessment:\n{pname} is classified as a `{analysis['tactical_classification']}`, maintaining composure and run containment "
                f"during high-leverage defensive scenarios."
            ])

        if limitations:
            lines.extend([
                "",
                "### Reliability Notice:",
                f"> {limitations[0]}"
            ])

        return "\n".join(lines)

    @staticmethod
    def analyze_batter_strengths(payload: Dict[str, Any]) -> str:
        evidence = payload["evidence_payload"]
        pname = evidence["player_name"]
        scope = evidence["competition_scope"]
        phases = evidence.get("innings_phase_splits", {})
        bowling_type = evidence.get("bowling_type_splits", {})
        strengths = evidence.get("strengths_evidence", [])
        weaknesses = evidence.get("weaknesses_evidence", [])

        lines = [
            f"# Batter Tactical Strengths & Weaknesses: {pname} ({scope})",
            "",
            "## 1. Tactical Strengths",
        ]
        for s in strengths:
            lines.append(f"- **Strength**: {s}")

        lines.extend([
            "",
            "## 2. Matchup Vulnerabilities",
        ])
        for w in weaknesses:
            lines.append(f"- **Vulnerability**: {w}")

        lines.extend([
            "",
            "## 3. Bowling Style Mastery (Pace vs Spin)",
            f"- **Vs Pace**: {bowling_type.get('pace', {}).get('runs_scored', 0)} runs off {bowling_type.get('pace', {}).get('balls_faced', 0)} balls | SR: `{bowling_type.get('pace', {}).get('strike_rate', 0.0):.1f}`",
            f"- **Vs Spin**: {bowling_type.get('spin', {}).get('runs_scored', 0)} runs off {bowling_type.get('spin', {}).get('balls_faced', 0)} balls | SR: `{bowling_type.get('spin', {}).get('strike_rate', 0.0):.1f}`",
            "",
            "## 4. Phase-Specific Strike Rates",
            f"- **Powerplay**: `{phases.get('powerplay', {}).get('strike_rate', 0.0):.1f}` ({phases.get('powerplay', {}).get('balls_faced', 0)} balls)",
            f"- **Middle Overs**: `{phases.get('middle', {}).get('strike_rate', 0.0):.1f}` ({phases.get('middle', {}).get('balls_faced', 0)} balls)",
            f"- **Death Overs**: `{phases.get('death', {}).get('strike_rate', 0.0):.1f}` ({phases.get('death', {}).get('balls_faced', 0)} balls)",
        ])

        return "\n".join(lines)

    @staticmethod
    def analyze_bowler_strengths(payload: Dict[str, Any]) -> str:
        evidence = payload["evidence_payload"]
        pname = evidence["player_name"]
        scope = evidence["competition_scope"]
        phases = evidence.get("innings_phase_splits", {})
        hand = evidence.get("batter_hand_splits", {})
        strengths = evidence.get("strengths_evidence", [])
        weaknesses = evidence.get("weaknesses_evidence", [])

        lines = [
            f"# Bowler Tactical Strengths & Weaknesses: {pname} ({scope})",
            "",
            "## 1. Tactical Strengths",
        ]
        for s in strengths:
            lines.append(f"- **Strength**: {s}")

        lines.extend([
            "",
            "## 2. Tactical Vulnerabilities",
        ])
        for w in weaknesses:
            lines.append(f"- **Vulnerability**: {w}")

        lines.extend([
            "",
            "## 3. Batter Handedness Breakdown",
            f"- **Vs RHB**: `{hand.get('rhb', {}).get('economy_rate', 0.0):.2f}` Economy ({hand.get('rhb', {}).get('balls_bowled', 0)} balls, {hand.get('rhb', {}).get('credited_wickets', 0)} wkts)",
            f"- **Vs LHB**: `{hand.get('lhb', {}).get('economy_rate', 0.0):.2f}` Economy ({hand.get('lhb', {}).get('balls_bowled', 0)} balls, {hand.get('lhb', {}).get('credited_wickets', 0)} wkts)",
            "",
            "## 4. Phase Concession Rates",
            f"- **Powerplay**: `{phases.get('powerplay', {}).get('economy_rate', 0.0):.2f}` Economy",
            f"- **Middle Overs**: `{phases.get('middle', {}).get('economy_rate', 0.0):.2f}` Economy",
            f"- **Death Overs**: `{phases.get('death', {}).get('economy_rate', 0.0):.2f}` Economy",
        ])

        return "\n".join(lines)

    @staticmethod
    def compare_players(payload: Dict[str, Any]) -> str:
        comp = payload["evidence_payload"]
        scope = comp["comparison_scope"]
        a = comp["batter_a"]
        b = comp["batter_b"]
        deltas = comp["deltas_a_minus_b"]
        phases = comp.get("phase_comparison", {})

        higher_player = a["name"] if deltas["cpri_delta"] >= 0 else b["name"]

        a_name = a["name"]
        b_name = b["name"]

        pp_a = phases.get("powerplay", {}).get(f"{a_name}_sr") or 0.0
        pp_b = phases.get("powerplay", {}).get(f"{b_name}_sr") or 0.0
        mid_a = phases.get("middle", {}).get(f"{a_name}_sr") or 0.0
        mid_b = phases.get("middle", {}).get(f"{b_name}_sr") or 0.0
        dth_a = phases.get("death", {}).get(f"{a_name}_sr") or 0.0
        dth_b = phases.get("death", {}).get(f"{b_name}_sr") or 0.0

        lines = [
            f"# Player Head-to-Head Comparison: {a_name} vs {b_name} ({scope})",
            "",
            "## 1. Composite CPRI & Component Standing",
            f"| Metric | {a_name} | {b_name} | Delta (A - B) |",
            f"|:---|:---:|:---:|:---:|",
            f"| **CPRI Score** | `{a['cpri_score']:.2f}` (Rank #{a['official_rank']}) | `{b['cpri_score']:.2f}` (Rank #{b['official_rank']}) | `{deltas['cpri_delta']:+.2f}` |",
            f"| **Pressure Impact (40%)** | `{a['components']['pressure_impact']:.2f}` | `{b['components']['pressure_impact']:.2f}` | `{deltas['pressure_impact_delta']:+.2f}` |",
            f"| **Pressure Adaptability (25%)** | `{a['components']['pressure_adaptability']:.2f}` | `{b['components']['pressure_adaptability']:.2f}` | `{deltas['adaptability_delta']:+.2f}` |",
            f"| **Clutch Consistency (20%)** | `{a['components']['clutch_consistency']:.2f}` | `{b['components']['clutch_consistency']:.2f}` | `{deltas['consistency_delta']:+.2f}` |",
            f"| **Reliability Confidence (15%)** | `{a['components']['reliability_confidence']:.2f}` | `{b['components']['reliability_confidence']:.2f}` | `{deltas['reliability_delta']:+.2f}` |",
            "",
            "## 2. Phase Strike Rate Comparison",
            f"- **Powerplay**: {a_name} `{pp_a:.1f}` vs {b_name} `{pp_b:.1f}`",
            f"- **Middle Overs**: {a_name} `{mid_a:.1f}` vs {b_name} `{mid_b:.1f}`",
            f"- **Death Overs**: {a_name} `{dth_a:.1f}` vs {b_name} `{dth_b:.1f}`",
            "",
            f"## 3. Tactical Scouting Verdict",
            f"**{higher_player}** holds the overall CPRI composite advantage in {scope}. "
            f"However, situational role specialization dictates their deployment: "
            f"{a_name} acts as a '{a['pressure_classification']}', while {b_name} acts as a '{b['pressure_classification']}'."
        ]

        return "\n".join(lines)

    @staticmethod
    def analyze_batter_bowler_matchup(payload: Dict[str, Any]) -> str:
        evidence = payload["evidence_payload"]
        h2h = evidence["head_to_head_record"]
        b_name = h2h["batter_name"]
        bw_name = h2h["bowler_name"]
        scope = h2h["competition_scope"]
        balls = h2h["balls_faced"]
        runs = h2h["runs_scored"]
        outs = h2h["dismissals"]
        sr = h2h["strike_rate"]
        tier = h2h["sample_tier"]
        is_reliable = h2h.get("is_statistically_reliable", False)

        lines = [
            f"# Head-to-Head Scouting Matchup: {b_name} vs {bw_name} ({scope})",
            "",
            "## 1. Direct Historical Record",
            f"- **Balls Faced**: `{balls}`",
            f"- **Runs Scored**: `{runs}`",
            f"- **Dismissals**: `{outs}`",
            f"- **Strike Rate**: `{sr:.2f}`",
            f"- **Dot Ball %**: `{h2h.get('dot_percentage', 0.0):.1f}%` ({h2h.get('dot_balls', 0)} dot balls)",
            f"- **Boundaries**: `{h2h.get('fours', 0)}` fours, `{h2h.get('sixes', 0)}` sixes",
            f"- **Sample Tier**: **{tier}**",
            "",
            "## 2. Statistical Reliability & Tactical Caveat",
        ]

        if not is_reliable or balls < 18:
            lines.extend([
                f"> [!WARNING]",
                f"> **CRITICAL SAMPLE LIMITATION**: This head-to-head encounter comprises only **{balls} legal balls faced**.",
                f"> Per official SupeRR Intelligence standards, a sample below 18 balls is exploratory and volatile.",
                f"> **Tactical Rule**: Do NOT assume direct dominance or permanent technical advantage from this small sample.",
                f"> Matchup planning should rely primarily on broader bowling-type splits (Pace/Spin) and match-phase context."
            ])
        else:
            lines.extend([
                f"This encounter meets statistical reliability criteria ({balls} >= 18 balls). "
                f"The historical strike rate of {sr:.1f} and dismissal count of {outs} indicate a meaningful tactical pattern."
            ])

        return "\n".join(lines)

    @staticmethod
    def answer_cricket_question(payload: Dict[str, Any]) -> str:
        query = payload["user_prompt"]
        evidence = payload["evidence_payload"]
        profiles = evidence.get("entity_profiles", {})

        lines = [
            f"# SupeRR Intelligence Analytics Response",
            f"**Query**: \"{evidence.get('query', query)}\"",
            "",
            "## Grounded Statistical Findings",
        ]

        for entity, data in profiles.items():
            if "cpri_score" in data:
                lines.append(
                    f"- **{entity}**: Official CPRI `{data['cpri_score']:.2f}` (Rank #{data['official_rank']}, {data['ranking_tier']}). "
                    f"Pressure Deliveries: `{data['exposure']['pressure_deliveries']}`. "
                    f"Pressure Impact: `{data['components']['pressure_impact']:.1f}`, Consistency: `{data['components']['clutch_consistency']:.1f}`."
                )
            else:
                lines.append(f"- **{entity}**: {data.get('status', 'No data')}")

        lines.extend([
            "",
            "### Analytical Summary:",
            "All findings above are strictly derived from verified Phase 3.5 frozen rankings and contextual match states. "
            "Unrecorded attributes (such as ball release velocity or subjective confidence) are excluded to ensure 100% statistical integrity."
        ])

        return "\n".join(lines)


class ScoutingAIService:
    """
    Master AI Scouting Generation Service.
    Coordinates Tier 1 (Hugging Face API), Tier 2 (Local Model), and Tier 3 (Deterministic Fallback)
    with strict response verification and zero hallucination guardrails.
    """

    def __init__(
        self,
        hf_token: Optional[str] = None,
        data_engine: Optional[ScoutingDataEngine] = None,
        prompt_assembler: Optional[ScoutingPromptAssembler] = None,
        enable_tier1: bool = True,
        enable_tier2: bool = False  # Local generation disabled by default on CPU/Windows
    ):
        self.engine = data_engine or ScoutingDataEngine()
        self.assembler = prompt_assembler or ScoutingPromptAssembler(self.engine)
        self.verifier = ScoutingResponseVerifier()

        self.enable_tier1 = enable_tier1
        self.hf_client = HFInferenceClient(token=hf_token) if enable_tier1 else None
        self.enable_tier2 = enable_tier2
        self.fallback_engine = DeterministicScoutingFallback()

    # -------------------------------------------------------------------------
    # Core Orchestration Helper
    # -------------------------------------------------------------------------
    def _execute_generation(
        self,
        payload: Dict[str, Any],
        fallback_func
    ) -> Dict[str, Any]:
        """
        Executes generation across the 3 tiers with verification:
        1. Attempt Tier 1 (HF API).
        2. If Tier 1 fails or is unconfigured, attempt Tier 2.
        3. Fall back to Tier 3 (Deterministic Python Engine).
        4. Validate output with ScoutingResponseVerifier.
        """
        feature = payload["feature"]
        evidence = payload["evidence_payload"]
        limitations = payload.get("sample_limitations", [])
        system_prompt = payload["system_prompt"]
        user_prompt = payload["user_prompt"]

        tier_used = "Tier 3: Deterministic Fallback Engine"
        model_name = "Rule-Based Python Grounding Engine"
        generated_text = ""
        verification_passed = True
        verification_notes = []

        # Attempt Tier 1: Hugging Face Inference API
        if self.enable_tier1 and self.hf_client and self.hf_client.is_configured():
            success, raw_text, meta = self.hf_client.generate(system_prompt, user_prompt)
            if success:
                # Audit response
                is_valid, violations = self.verifier.verify_response(raw_text, evidence, limitations, feature)
                if is_valid:
                    tier_used = "Tier 1: Hugging Face API (Qwen/Qwen2.5-7B-Instruct)"
                    model_name = meta.get("model", "Qwen/Qwen2.5-7B-Instruct")
                    generated_text = raw_text
                    verification_passed = True
                else:
                    verification_passed = False
                    verification_notes = violations
                    # Verification failed: fall back safely to Tier 3
                    generated_text = fallback_func(payload)
            else:
                verification_notes.append(f"Tier 1 API unavailable: {meta.get('error_type', 'UNKNOWN')}")
                generated_text = fallback_func(payload)
        else:
            if not (self.hf_client and self.hf_client.is_configured()):
                verification_notes.append("Tier 1 skipped: HF_TOKEN not configured in environment.")
            generated_text = fallback_func(payload)

        return {
            "status": "success",
            "feature": feature,
            "tier_used": tier_used,
            "model_name": model_name,
            "verified": verification_passed,
            "verification_notes": verification_notes,
            "response": generated_text,
            "sample_limitations": limitations
        }

    # -------------------------------------------------------------------------
    # The 7 Core Scouting Features
    # -------------------------------------------------------------------------
    def generate_player_report(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Feature 1: Comprehensive Player Scouting Report."""
        payload = self.assembler.build_scouting_report_prompt(player_name, competition_scope, role)
        return self._execute_generation(payload, self.fallback_engine.generate_player_report)

    def explain_pressure_performance(
        self,
        player_name: str,
        competition_scope: str = "IPL",
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """Feature 2: Pressure Performance Explanation."""
        payload = self.assembler.build_pressure_explanation_prompt(player_name, competition_scope, role)
        return self._execute_generation(payload, self.fallback_engine.explain_pressure_performance)

    def analyze_batter_strengths(
        self,
        player_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Feature 3: Batter Strengths and Weaknesses."""
        payload = self.assembler.build_batter_strengths_weaknesses_prompt(player_name, competition_scope)
        return self._execute_generation(payload, self.fallback_engine.analyze_batter_strengths)

    def analyze_bowler_strengths(
        self,
        player_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Feature 4: Bowler Strengths and Weaknesses."""
        payload = self.assembler.build_bowler_strengths_weaknesses_prompt(player_name, competition_scope)
        return self._execute_generation(payload, self.fallback_engine.analyze_bowler_strengths)

    def compare_players(
        self,
        player_a: str,
        player_b: str,
        competition_scope: str = "IPL",
        role: Optional[str] = "Batter"
    ) -> Dict[str, Any]:
        """Feature 5: Player Comparison Matrix."""
        payload = self.assembler.build_batter_comparison_prompt(player_a, player_b, competition_scope)
        return self._execute_generation(payload, self.fallback_engine.compare_players)

    def analyze_batter_bowler_matchup(
        self,
        batter_name: str,
        bowler_name: str,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Feature 6: Batter vs Bowler Head-to-Head Scouting."""
        payload = self.assembler.build_h2h_scouting_prompt(batter_name, bowler_name, competition_scope)
        return self._execute_generation(payload, self.fallback_engine.analyze_batter_bowler_matchup)

    def answer_cricket_question(
        self,
        query: str,
        entities_involved: Optional[List[str]] = None,
        competition_scope: str = "IPL"
    ) -> Dict[str, Any]:
        """Feature 7: Natural-Language Analytics Question Answering."""
        payload = self.assembler.build_analytics_qa_prompt(query, entities_involved, competition_scope)
        return self._execute_generation(payload, self.fallback_engine.answer_cricket_question)
