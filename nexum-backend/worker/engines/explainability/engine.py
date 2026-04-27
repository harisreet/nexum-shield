"""
NEXUM SHIELD — Explainability Engine
Attempts to generate an explanation using Gemini API for natural, context-aware reasoning.
If Gemini fails or no API key is provided, falls back to deterministic rule-based template.
"""
from typing import Any
import structlog

from config import settings
from engines.base import Engine, EngineError

try:
    from google import genai
except ImportError:
    genai = None

log = structlog.get_logger()

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
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        risk_score: float = input_data.get("risk_score", 0.0)
        signals: list[str] = input_data.get("signals", [])
        candidates: list[dict] = input_data.get("candidates", [])
        decision: str = input_data.get("decision", "ALLOW")

        # Try Gemini first, fallback to rules
        explanation = self._generate_with_gemini(risk_score, signals, candidates, decision)
        if not explanation:
            explanation = self._generate_rule_based(risk_score, signals, candidates, decision)

        return {"explanation": explanation}

    def _generate_with_gemini(self, score: float, signals: list[str], candidates: list[dict], decision: str) -> str | None:
        if not settings.GEMINI_API_KEY or genai is None:
            return None

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            prompt = (
                f"You are the Nexum Shield AI integrity platform. Briefly explain why an asset received the decision: {decision}.\n"
                f"Context:\n"
                f"- Risk Score: {score:.2%}\n"
                f"- Active Risk Signals: {', '.join(signals) if signals else 'None'}\n"
                f"- Number of known reference matches found: {len(candidates)}\n\n"
                "Write a concise, professional 1-3 sentence explanation for a trust and safety moderator. "
                "Do not mention 'Gemini' or act like an assistant. Just provide the direct explanation."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            return response.text.strip()
        except Exception as e:
            log.warning("explainability.gemini_failed", error=str(e))
            return None  # Trigger fallback

    def _generate_rule_based(self, score: float, signals: list[str], candidates: list[dict], decision: str) -> str:
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
