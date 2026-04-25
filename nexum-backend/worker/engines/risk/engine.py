"""
NEXUM SHIELD — Risk Engine
Deterministic risk scoring. No randomness. No ML. No ambiguity.

HARD RULE: risk_score = max(candidate_scores)
"""
from typing import Any

from config import settings
from engines.base import Engine, EngineError


class RiskEngine(Engine):
    """
    Input:  { "candidates": [{"id": str, "score": float}] }
    Output: { "risk_score": float, "signals": list[str] }

    Signal definitions:
      - "high_similarity"   : risk_score >= RISK_REVIEW_THRESHOLD (0.70)
      - "near_duplicate"    : risk_score >= UNCERTAINTY_LOWER (0.85)
      - "block_threshold"   : risk_score >= RISK_BLOCK_THRESHOLD (0.90)
      - "no_matches"        : index was empty or no candidates found
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        candidates: list[dict] = input_data.get("candidates", [])

        # ── HARD RULE: deterministic scoring ─────────────────────
        if not candidates:
            risk_score = 0.0
            signals = ["no_matches"]
        else:
            risk_score = max(c["score"] for c in candidates)
            signals = self._compute_signals(risk_score)

        return {
            "risk_score": round(risk_score, 6),  # 6 decimal determinism
            "signals": signals,
        }

    def _compute_signals(self, score: float) -> list[str]:
        signals: list[str] = []

        if score >= settings.RISK_BLOCK_THRESHOLD:
            signals.append("block_threshold")
        if score >= settings.UNCERTAINTY_LOWER:
            signals.append("near_duplicate")
        if score >= settings.RISK_REVIEW_THRESHOLD:
            signals.append("high_similarity")

        return signals
