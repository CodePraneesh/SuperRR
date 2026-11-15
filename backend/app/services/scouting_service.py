"""
backend/app/services/scouting_service.py
Service coordinator wrapping ScoutingDataEngine and ScoutingAIService
for FastAPI dependency injection and route handlers.
"""
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    PlayerNotFoundError,
    InvalidScopeError,
    InvalidRoleError,
    validate_scope,
    validate_role
)
from scouting_data_engine import ScoutingDataEngine
from scouting_prompt_assembler import ScoutingPromptAssembler
from scouting_ai_service import ScoutingAIService


class ScoutingService:
    """
    Singleton service layer providing access to frozen data stores,
    prompt assembly, and multi-tier AI scouting generation.
    """

    def __init__(self, data_dir: Optional[Path] = None, hf_token: Optional[str] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.hf_token = hf_token if hf_token is not None else settings.HF_TOKEN
        
        # Initialize engines
        self.engine = ScoutingDataEngine(data_dir=self.data_dir)
        self.assembler = ScoutingPromptAssembler(self.engine)
        self.ai_service = ScoutingAIService(
            hf_token=self.hf_token,
            data_engine=self.engine,
            prompt_assembler=self.assembler,
            enable_tier1=bool(self.hf_token)
        )

    # -------------------------------------------------------------------------
    # System Status & Health
    # -------------------------------------------------------------------------
    def get_health_status(self) -> Dict[str, Any]:
        """Returns runtime health, store status, and tier capability."""
        stores_loaded = (
            bool(self.engine.profiles_store) and
            bool(self.engine.splits_store) and
            (self.data_dir / "head_to_head_matrix.json").exists() and
            bool(self.engine.official_store)
        )
        is_offline = not bool(self.hf_token)
        tier_avail = (
            "Tier 1: Hugging Face API (Qwen/Qwen2.5-7B-Instruct)"
            if bool(self.hf_token)
            else "Tier 3: Deterministic Fallback Engine (Offline Safe)"
        )
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "stores_loaded": stores_loaded,
            "offline_mode": is_offline,
            "tier_available": tier_avail,
            "data_dir": str(self.data_dir),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    # -------------------------------------------------------------------------
    # Official Unified Rankings (Phase 8 Baseline)
    # -------------------------------------------------------------------------
    def get_official_rankings(self, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the authoritative competition Top 10 rankings and candidate pool.
        """
        return self.engine.get_official_rankings(role=role)

    def get_official_player(self, name: str) -> Dict[str, Any]:
        """
        Retrieves official player record with 90% bootstrap rank CI.
        """
        player = self.engine.get_official_player(name)
        if not player:
            raise PlayerNotFoundError(name, "Official", "Unified")
        return player

    # -------------------------------------------------------------------------
    # Cohort Players (Contextual League View)
    # -------------------------------------------------------------------------
    def get_cohort_players(
        self,
        scope: str,
        role: str,
        official_only: bool = False,
        confidence_tier: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieves list of players in a specific cohort with optional filtering.
        """
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)
        cohort_key = f"{validated_scope} {validated_role}s"

        all_players = self.engine._cohort_players.get(cohort_key, [])
        if not all_players:
            # Fallback if key differs
            all_players = [
                p for p in self.engine.profiles_store.get("profiles", [])
                if p["competition_scope"].upper() == validated_scope
                and p["role"].capitalize() == validated_role
            ]

        # Apply filters
        filtered = []
        for p in all_players:
            is_top10 = p.get("is_official_top10", False)
            if official_only and not is_top10:
                continue
            if confidence_tier and p.get("confidence_tier", "").lower() != confidence_tier.lower():
                continue
            
            perf = p.get("performance_stats", {})
            sr = perf.get("strike_rate") if validated_role == "Batter" else None
            econ = perf.get("economy_rate") if validated_role == "Bowler" else None

            item = {
                "player_id": p.get("player_id"),
                "player_name": p["player_name"],
                "competition_scope": p["competition_scope"],
                "role": p["role"],
                "cohort": p.get("cohort", cohort_key),
                "official_rank": p.get("official_rank"),
                "ranking_tier": p.get("ranking_tier", "Unranked"),
                "confidence_tier": p.get("confidence_tier", "Low"),
                "is_official_top10": is_top10,
                "is_official_ranked": is_top10,
                "cpri_score": p.get("cpri_score", 0.0),
                "components": p.get("components", {}),
                "pressure_deliveries": p.get("exposure", {}).get("pressure_deliveries", 0),
                "strike_rate": sr,
                "economy_rate": econ
            }
            filtered.append(item)

        total = len(filtered)
        official_count = sum(1 for p in filtered if p["is_official_top10"])
        paginated = filtered[offset : offset + limit]

        return {
            "competition_scope": validated_scope,
            "role": validated_role,
            "cohort": cohort_key,
            "view_type": "contextual_league_view",
            "disclaimer": "Contextual league view, not the official ranking. The authoritative competition ranking is the Unified Phase 8 ranking at /api/v1/official.",
            "total_players": total,
            "official_count": official_count,
            "limit": limit,
            "offset": offset,
            "players": paginated
        }

    # -------------------------------------------------------------------------
    # Single Player Profile & Splits
    # -------------------------------------------------------------------------
    def get_player_profile(self, name: str, scope: str, role: str) -> Dict[str, Any]:
        """Retrieves full player profile including peer percentiles and empirical strengths."""
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)

        profile = self.engine.get_player_profile(
            player_name=name,
            competition_scope=validated_scope,
            role=validated_role
        )
        if not profile:
            off_p = self.engine.get_official_player(name)
            if off_p and off_p["role"].capitalize() == validated_role:
                p_stats = off_p.get("pressure_stats", {})
                profile = {
                    "player_id": off_p["player_id"],
                    "player_name": off_p["player_name"],
                    "competition_scope": validated_scope,
                    "role": off_p["role"],
                    "cohort": f"Official {off_p['role']}s",
                    "official_rank": off_p["official_rank"],
                    "ranking_tier": f"Official Top 10 #{off_p['official_rank']}" if off_p.get("is_official_top10") else f"Candidate #{off_p['official_rank']}",
                    "confidence_tier": off_p.get("confidence_tier", "High Confidence"),
                    "is_official_top10": off_p.get("is_official_top10", False),
                    "is_official_ranked": off_p.get("is_official_top10", False),
                    "cpri_score": off_p["cpri_score"],
                    "components": off_p["components"],
                    "exposure": {
                        "pressure_deliveries": p_stats.get("pressure_deliveries", 0),
                        "pressure_matches": p_stats.get("pressure_matches", 0),
                        "pos_pressure_match_ratio": 0.65,
                        "total_deliveries": p_stats.get("total_deliveries", 0),
                        "total_matches": p_stats.get("total_matches", 0)
                    },
                    "performance_stats": {
                        "strike_rate": p_stats.get("pressure_strike_rate"),
                        "economy_rate": p_stats.get("pressure_economy")
                    }
                }
            else:
                raise PlayerNotFoundError(name, validated_scope, validated_role)

        # Attach peer benchmarks & strengths
        try:
            benchmarks = self.engine.get_peer_comparisons(
                player_name=name,
                competition_scope=validated_scope,
                role=validated_role
            )
        except Exception:
            benchmarks = None

        try:
            sw = self.engine.get_strengths_and_weaknesses(
                player_name=name,
                competition_scope=validated_scope,
                role=validated_role
            )
        except Exception:
            sw = None

        res = dict(profile)
        res["is_official_ranked"] = profile.get("is_official_top10", False)
        res["peer_benchmarks"] = benchmarks
        res["strengths_and_weaknesses"] = sw
        return res

    def get_player_splits(self, name: str, scope: str, role: str) -> Dict[str, Any]:
        """Retrieves player phase and pressure splits."""
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)

        splits = self.engine.get_contextual_splits(
            player_name=name,
            competition_scope=validated_scope,
            role=validated_role
        )
        if not splits:
            off_p = self.engine.get_official_player(name)
            if off_p and off_p.get("contextual_splits"):
                cs = off_p["contextual_splits"]
                splits = cs.get(validated_scope) or (list(cs.values())[0] if isinstance(list(cs.values())[0], dict) and "innings_phase_splits" in list(cs.values())[0] else cs)
            elif off_p:
                splits = {
                    "player_name": name,
                    "competition_scope": validated_scope,
                    "role": validated_role,
                    "innings_phase_splits": {},
                    "pressure_contrast": {"tactical_classification": off_p.get("tactical_classification", "Balanced Execution")}
                }
            else:
                raise PlayerNotFoundError(name, validated_scope, validated_role)

        return {
            "player_name": splits.get("player_name", name),
            "competition_scope": splits.get("competition_scope", validated_scope),
            "role": splits.get("role", validated_role),
            "innings_phase_splits": splits.get("innings_phase_splits", {}),
            "pressure_contrast": splits.get("pressure_contrast", {}),
            "bowling_type_splits": splits.get("bowling_type_splits") if validated_role == "Batter" else None,
            "batter_hand_splits": splits.get("batter_hand_splits") if validated_role == "Bowler" else None
        }

    # -------------------------------------------------------------------------
    # AI Scouting Reports
    # -------------------------------------------------------------------------
    def get_scouting_report(self, name: str, scope: str, role: str) -> Dict[str, Any]:
        """Generates evidence-grounded AI scouting report for player."""
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)

        # Check existence first
        profile = self.get_player_profile(name, scope=validated_scope, role=validated_role)
        if not profile:
            raise PlayerNotFoundError(name, validated_scope, validated_role)

        gen_result = self.ai_service.generate_player_report(
            player_name=name,
            competition_scope=validated_scope,
            role=validated_role
        )

        return {
            "status": gen_result.get("status", "success"),
            "player_name": name,
            "competition_scope": validated_scope,
            "role": validated_role,
            "feature": gen_result.get("feature", "player_scouting_report"),
            "tier_used": gen_result.get("tier_used", ""),
            "model_name": gen_result.get("model_name", ""),
            "verified": gen_result.get("verified", True),
            "verification_notes": gen_result.get("verification_notes", []),
            "response": gen_result.get("response", ""),
            "sample_limitations": gen_result.get("sample_limitations", [])
        }

    def get_pressure_explanation(self, name: str, scope: str, role: str) -> Dict[str, Any]:
        """Generates deep explanation of player's pressure performance."""
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)

        profile = self.get_player_profile(name, scope=validated_scope, role=validated_role)
        if not profile:
            raise PlayerNotFoundError(name, validated_scope, validated_role)

        gen_result = self.ai_service.explain_pressure_performance(
            player_name=name,
            competition_scope=validated_scope,
            role=validated_role
        )

        return {
            "status": gen_result.get("status", "success"),
            "player_name": name,
            "competition_scope": validated_scope,
            "role": validated_role,
            "feature": gen_result.get("feature", "explain_pressure_performance"),
            "tier_used": gen_result.get("tier_used", ""),
            "model_name": gen_result.get("model_name", ""),
            "verified": gen_result.get("verified", True),
            "verification_notes": gen_result.get("verification_notes", []),
            "response": gen_result.get("response", ""),
            "sample_limitations": gen_result.get("sample_limitations", [])
        }

    # -------------------------------------------------------------------------
    # Comparison
    # -------------------------------------------------------------------------
    def compare_players(
        self,
        player_a: str,
        player_b: str,
        scope: str = "IPL",
        role: str = "Batter"
    ) -> Dict[str, Any]:
        """Conducts side-by-side player comparison with CPRI component deltas and narrative."""
        validated_scope = validate_scope(scope)
        validated_role = validate_role(role)

        # Check both players exist
        prof_a = self.engine.get_player_profile(player_a, competition_scope=validated_scope, role=validated_role)
        if not prof_a:
            raise PlayerNotFoundError(player_a, validated_scope, validated_role)
        prof_b = self.engine.get_player_profile(player_b, competition_scope=validated_scope, role=validated_role)
        if not prof_b:
            raise PlayerNotFoundError(player_b, validated_scope, validated_role)

        # Structured comparison
        if validated_role == "Batter":
            structured = self.engine.compare_batters(player_a, player_b, competition_scope=validated_scope)
            ai_res = self.ai_service.compare_players(player_a, player_b, competition_scope=validated_scope, role="Batter")
        else:
            # Bowler structured comparison
            comp_a = prof_a["components"]
            comp_b = prof_b["components"]
            deltas = {
                "cpri_delta": round(prof_a["cpri_score"] - prof_b["cpri_score"], 2),
                "pressure_impact_delta": round(comp_a["pressure_impact"] - comp_b["pressure_impact"], 2),
                "adaptability_delta": round(comp_a["pressure_adaptability"] - comp_b["pressure_adaptability"], 2),
                "consistency_delta": round(comp_a["clutch_consistency"] - comp_b["clutch_consistency"], 2),
                "reliability_delta": round(comp_a["reliability_confidence"] - comp_b["reliability_confidence"], 2)
            }
            splits_a = self.engine.get_contextual_splits(player_a, competition_scope=validated_scope, role="Bowler")
            splits_b = self.engine.get_contextual_splits(player_b, competition_scope=validated_scope, role="Bowler")
            structured = {
                "comparison_scope": validated_scope,
                "role": "Bowler",
                "bowler_a": {
                    "name": prof_a["player_name"],
                    "official_rank": prof_a.get("official_rank"),
                    "cpri_score": prof_a["cpri_score"],
                    "components": comp_a,
                    "overall_economy": prof_a["performance_stats"].get("economy_rate")
                },
                "bowler_b": {
                    "name": prof_b["player_name"],
                    "official_rank": prof_b.get("official_rank"),
                    "cpri_score": prof_b["cpri_score"],
                    "components": comp_b,
                    "overall_economy": prof_b["performance_stats"].get("economy_rate")
                },
                "deltas_a_minus_b": deltas
            }
            # AI summary query
            ai_res = self.ai_service.answer_cricket_question(
                query=f"Compare {player_a} and {player_b} as bowlers in {validated_scope}",
                entities_involved=[player_a, player_b],
                competition_scope=validated_scope
            )

        return {
            "status": "success",
            "comparison_scope": validated_scope,
            "role": validated_role,
            "player_a": player_a,
            "player_b": player_b,
            "structured_comparison": structured,
            "ai_analysis": ai_res.get("response", ""),
            "tier_used": ai_res.get("tier_used", "Tier 3: Deterministic Fallback Engine"),
            "model_name": ai_res.get("model_name", "Rule-Based Python Grounding Engine"),
            "verified": ai_res.get("verified", True),
            "verification_notes": ai_res.get("verification_notes", []),
            "sample_limitations": ai_res.get("sample_limitations", [])
        }

    # -------------------------------------------------------------------------
    # Head-to-Head Matchup
    # -------------------------------------------------------------------------
    def get_matchup(self, batter: str, bowler: str, scope: str = "IPL") -> Dict[str, Any]:
        """Retrieves head-to-head records and narrative analysis with small-sample warnings."""
        validated_scope = validate_scope(scope)
        h2h_record = self.engine.get_head_to_head(batter, bowler, competition_scope=validated_scope)
        ai_res = self.ai_service.analyze_batter_bowler_matchup(batter, bowler, competition_scope=validated_scope)

        balls = h2h_record.get("balls_faced", 0)
        is_small = balls < 18
        warning = (
            f"Sample size is exploratory ({balls} balls < 18 balls). "
            f"Statistical conclusions should be treated with caution."
            if is_small else None
        )

        return {
            "status": "success",
            "competition_scope": validated_scope,
            "batter_name": batter,
            "bowler_name": bowler,
            "h2h_data": h2h_record,
            "ai_narrative": ai_res.get("response", ""),
            "tier_used": ai_res.get("tier_used", "Tier 3: Deterministic Fallback Engine"),
            "model_name": ai_res.get("model_name", "Rule-Based Python Grounding Engine"),
            "verified": ai_res.get("verified", True),
            "is_small_sample": is_small,
            "sample_tier": h2h_record.get("sample_tier", "Unknown"),
            "sample_warning": warning
        }

    # -------------------------------------------------------------------------
    # Natural Language QA
    # -------------------------------------------------------------------------
    def ask_analytics_question(
        self,
        query: str,
        scope: Optional[str] = None,
        role: Optional[str] = None,
        target_entities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Answers cricket analytics questions strictly grounded in verified Phase 3.5 stats."""
        validated_scope = validate_scope(scope) if scope else "IPL"
        ai_res = self.ai_service.answer_cricket_question(
            query=query,
            entities_involved=target_entities,
            competition_scope=validated_scope
        )

        return {
            "status": ai_res.get("status", "success"),
            "query": query,
            "scope": validated_scope,
            "answer": ai_res.get("response", ""),
            "tier_used": ai_res.get("tier_used", "Tier 3: Deterministic Fallback Engine"),
            "model_name": ai_res.get("model_name", "Rule-Based Python Grounding Engine"),
            "verified": ai_res.get("verified", True),
            "verification_notes": ai_res.get("verification_notes", []),
            "evidence_summary": ai_res.get("evidence_summary")
        }
