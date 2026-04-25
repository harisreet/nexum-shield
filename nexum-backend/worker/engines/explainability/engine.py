"""
NEXUM SHIELD — Explainability Engine
Generates a bounded, deterministic explanation from risk data.
ZERO external API calls. Rule-based template only.
No hallucination possible. Every explanation is reproducible.
"""
from typing import Any

from config import settings
from engines.base import Engine, EngineError


# ─── Explanation templates (keyed by decision) ────────────────────
TEMPLATES = {
    "BLOCK": (
        "BLOCKED: The submitted asset has a similarity score of {score:.2%} against "
        "known reference material (threshold: {block_threshold:.0%}). "
        "Active signals: {signals}. {match_summary} "
        "Policy v{policy_version}: assets exceeding the block threshold are rejected "
        "to prevent unauthorized distribution."
    ),
    "REVIEW": (
        "FLAGGED FOR REVIEW: The submitted asset matched reference material at {score:.2%} similarity. "
        "{uncertainty_note}"
        "Active signals: {signals}. {match_summary} "
        "Policy v{policy_version}: assets in the review band require manual verification."
    ),
    "ALLOW": (
        "ALLOWED: The submitted asset has a maximum similarity score of {score:.2%} "
        "against {num_candidates} reference candidate(s). "
        "No signals exceeded review thresholds. "
        "Policy v{policy_version}: asset is cleared for distribution."
    ),
}

UNCERTAINTY_NOTE = (
    "The score falls within the uncertainty band "
    f"({settings.UNCERTAINTY_LOWER:.0%}–{settings.UNCERTAINTY_UPPER:.0%}), "
    "triggering a mandatory review regardless of signal count. "
)


class ExplainabilityEngine(Engine):
    """
    Input:  { "risk_score": float, "signals": list[str],
              "candidates": list[dict], "decision": str }
    Output: { "explanation": str }

    Constraints:
      - Uses ONLY: risk_score, signals, candidates, decision
      - No external calls
      - Deterministic: same inputs → same explanation
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        risk_score: float = input_data.get("risk_score", 0.0)
        signals: list[str] = input_data.get("signals", [])
        candidates: list[dict] = input_data.get("candidates", [])
        decision: str = input_data.get("decision", "ALLOW")

        explanation = self._generate(risk_score, signals, candidates, decision)

        return {"explanation": explanation}

    def _generate(
        self,
        score: float,
        signals: list[str],
        candidates: list[dict],
        decision: str,
    ) -> str:
        template = TEMPLATES.get(decision, TEMPLATES["ALLOW"])

        # ── Match summary ─────────────────────────────────────────
        if candidates:
            top = candidates[0]
            match_summary = (
                f"Top match: asset {top['id'][:8]}... "
                f"with score {top['score']:.2%}."
            )
        else:
            match_summary = "No reference matches found in index."

        # ── Uncertainty note ──────────────────────────────────────
        in_uncertainty_band = (
            settings.UNCERTAINTY_LOWER <= score < settings.UNCERTAINTY_UPPER
        )
        uncertainty_note = UNCERTAINTY_NOTE if in_uncertainty_band else ""

        # ── Signal string ─────────────────────────────────────────
        signal_str = ", ".join(signals) if signals else "none"

        return template.format(
            score=score,
            block_threshold=settings.RISK_BLOCK_THRESHOLD,
            signals=signal_str,
            match_summary=match_summary,
            policy_version=settings.POLICY_VERSION,
            num_candidates=len(candidates),
            uncertainty_note=uncertainty_note,
        )
