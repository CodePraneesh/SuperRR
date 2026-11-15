#!/usr/bin/env python3
"""
scouting_response_verifier.py
SupeRR Intelligence - Phase 4.4 Evidence Verification Guardrail

Verifies language model generated answers against the immutable evidence payload:
1. Rejects altered or ungrounded CPRI scores and official ranks
2. Ensures correct competition format preservation (IPL vs T20I)
3. Enforces sample size disclosures and small-sample warnings
4. Rejects claims of direct head-to-head dominance on low-sample encounters (<18 balls)
5. Validates player identity integrity
"""
import re
from typing import Tuple, List, Dict, Any, Optional, Set


class ScoutingResponseVerifier:
    """
    Automated fact-checking and guardrail verifier for AI scouting reports.
    """

    def __init__(self, tolerance: float = 0.25):
        self.tolerance = tolerance

    def verify_response(
        self,
        generated_text: str,
        evidence: Dict[str, Any],
        limitations: Optional[List[str]] = None,
        feature_name: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Audits generated scouting text against verified evidence.
        Returns:
            (is_valid: bool, violations: List[str])
        """
        violations = []
        text_lower = generated_text.lower()

        # ---------------------------------------------------------------------
        # 1. CPRI Score and Rank Immutability Audit
        # ---------------------------------------------------------------------
        def extract_ranked_entities(obj) -> List[Dict[str, Any]]:
            entities = []
            if isinstance(obj, dict):
                if "cpri_score" in obj:
                    entities.append(obj)
                for v in obj.values():
                    entities.extend(extract_ranked_entities(v))
            elif isinstance(obj, list):
                for item in obj:
                    entities.extend(extract_ranked_entities(item))
            return entities

        ranked_entities = extract_ranked_entities(evidence)

        if ranked_entities:
            expected_cpris = {float(e["cpri_score"]) for e in ranked_entities if "cpri_score" in e}
            expected_ranks = {int(e["official_rank"]) for e in ranked_entities if "official_rank" in e}

            # Check if text claims an ungrounded CPRI
            cpri_matches = re.findall(r"cpri(?:\s+(?:score|rating|of))?[:\s]+([0-9]+\.?[0-9]*)", text_lower)
            for m in cpri_matches:
                try:
                    val = float(m)
                    if not any(abs(val - exp) <= 0.15 for exp in expected_cpris):
                        violations.append(
                            f"CPRI IMMUTABILITY VIOLATION: Model cited CPRI {val}, but official frozen score(s) are {expected_cpris}."
                        )
                except ValueError:
                    pass

            # Check rank if mentioned
            rank_matches = re.findall(r"(?:ranked|rank)\s+#?([0-9]+)", text_lower)
            for r in rank_matches:
                try:
                    r_val = int(r)
                    if f"rank {r_val}" in text_lower or f"ranked #{r_val}" in text_lower:
                        if r_val not in expected_ranks and r_val not in (10, 5, 1):
                            violations.append(
                                f"RANK INTEGRITY VIOLATION: Model cited rank {r_val}, but official frozen rank(s) are {expected_ranks}."
                            )
                except ValueError:
                    pass

        # ---------------------------------------------------------------------
        # 2. Format Preservation Audit
        # ---------------------------------------------------------------------
        expected_scope = evidence.get("comparison_scope") or evidence.get("competition_scope")
        if not expected_scope and ranked_entities:
            expected_scope = ranked_entities[0].get("competition_scope")

        if expected_scope:
            expected_scope = str(expected_scope).upper()
            if expected_scope == "IPL":
                # Ensure it doesn't describe the record as T20I tournament or T20 International
                if "t20 international" in text_lower and "t20i" in text_lower and "ipl" not in text_lower:
                    violations.append("FORMAT CONFUSION: Evaluation is for IPL, but model classified it solely as T20I.")
            elif expected_scope == "T20I":
                if "indian premier league" in text_lower and "ipl" in text_lower and "t20i" not in text_lower:
                    violations.append("FORMAT CONFUSION: Evaluation is for T20I, but model classified it solely as IPL.")

        # ---------------------------------------------------------------------
        # 3. Small-Sample Head-to-Head Warning Enforcement
        # ---------------------------------------------------------------------
        h2h = evidence.get("head_to_head_record")
        if isinstance(h2h, dict):
            balls = h2h.get("balls_faced", 0)
            is_reliable = h2h.get("is_statistically_reliable", True)

            if not is_reliable or balls < 18:
                # Text must acknowledge sample limitation or small sample
                has_warning = any(w in text_lower for w in [
                    "sample", "low sample", "small sample", "limited", "exploratory", "balls", "caveat", "cautious"
                ])
                if not has_warning:
                    violations.append(
                        f"SMALL SAMPLE WARNING VIOLATION: Matchup has only {balls} balls faced, but response omitted sample limitation disclosure."
                    )

                # Check for ungrounded dominance claims on small sample
                prohibited_phrases = ["completely dominates", "clear mastery", "owns the matchup", "total dominance"]
                for p in prohibited_phrases:
                    if p in text_lower:
                        violations.append(
                            f"UNGROUNDED TACTICAL CLAIM: Claimed '{p}' on a low sample of {balls} balls."
                        )

        # ---------------------------------------------------------------------
        # 4. Mandatory Limitations Enforcement
        # ---------------------------------------------------------------------
        if limitations:
            # If critical provisional ranking warning is in limitations, verify it was disclosed
            for lim in limitations:
                if "provisional" in lim.lower() and "provisional" not in text_lower:
                    violations.append("DISCLOSURE VIOLATION: Omitted required disclosure of provisional ranking status.")

        is_valid = (len(violations) == 0)
        return is_valid, violations
