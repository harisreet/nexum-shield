"""
NEXUM SHIELD — Decision Engine
Policy-table driven. Deterministic. No randomness.

LOCKED POLICY (v1):
  risk_score >= 0.90               → BLOCK
  0.85 <= risk_score < 0.90        → REVIEW  (uncertainty guard — FORCED)
  0.70 <= risk_score < 0.85        → REVIEW
  risk_score < 0.70                → ALLOW
"""
from typing import Any, Literal

from config import settings
from engines.base import Engine, EngineError

Decision = Literal["ALLOW", "REVIEW", "BLOCK"]


class DecisionEngine(Engine):
    """
    Input:  { "risk_score": float, "signals": list[str] }
    Output: { "decision": "ALLOW"|"REVIEW"|"BLOCK",
              "policy_version": str, "thresholds": dict }
    """

    THRESHOLDS = {
        "review": settings.RISK_REVIEW_THRESHOLD,
        "block": settings.RISK_BLOCK_THRESHOLD,
        "uncertainty_lower": settings.UNCERTAINTY_LOWER,
        "uncertainty_upper": settings.UNCERTAINTY_UPPER,
    }

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        risk_score: float = input_data.get("risk_score", 0.0)

        decision = self._apply_policy(risk_score)

        return {
            "decision": decision,
            "policy_version": settings.POLICY_VERSION,
            "thresholds": self.THRESHOLDS,
        }

    def _apply_policy(self, score: float) -> Decision:
        """
        Strict policy table. Order of conditions matters — do not reorder.
        BLOCK is checked first (highest confidence required).
        """
        if score >= settings.RISK_BLOCK_THRESHOLD:
            return "BLOCK"

        if settings.UNCERTAINTY_LOWER <= score < settings.UNCERTAINTY_UPPER:
            # Uncertainty guard: force REVIEW, never ALLOW in ambiguous band
            return "REVIEW"

        if score >= settings.RISK_REVIEW_THRESHOLD:
            return "REVIEW"

        return "ALLOW"
