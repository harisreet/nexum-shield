"""
NEXUM SHIELD — Pipeline Orchestrator (pHash Edition)
Ties all engines together in strict order. No business logic.
Each stage is isolated — failure in any stage aborts the pipeline.
"""
import uuid
from datetime import datetime
from typing import Any

import structlog

from engines.preprocessing.processor import PreprocessingEngine
from engines.embedding.engine import EmbeddingEngine
from engines.matching.engine import MatchingEngine
from engines.risk.engine import RiskEngine
from engines.decision.engine import DecisionEngine
from engines.explainability.engine import ExplainabilityEngine
from engines.base import EngineError
from config import settings

log = structlog.get_logger()

# ─── Singleton engine instances ───────────────────────────────────
_preprocessing = PreprocessingEngine()
_embedding = EmbeddingEngine()
_matching = MatchingEngine()
_risk = RiskEngine()
_decision = DecisionEngine()
_explainability = ExplainabilityEngine()


async def run_pipeline(
    image_bytes: bytes,
    filename: str,
    asset_id: str,
    trace_id: str,
) -> dict[str, Any]:
    """
    Execute the full 6-stage pipeline using pHash matching.
    Returns a complete AnalysisResponse-compatible dict.
    Raises EngineError on any stage failure.

    Pipeline:
      1. Preprocessing      (validation + pHash)
      2. Embedding          (pHash fingerprint)
      3. Matching           (Hamming distance search)
      4. Risk scoring       (deterministic)
      5. Decision           (policy table)
      6. Explainability     (rule-based audit)
    """
    ctx = log.bind(trace_id=trace_id, asset_id=asset_id)
    ctx.info("pipeline.start")

    # ── Stage 1: Preprocessing ────────────────────────────────────
    ctx.info("pipeline.preprocessing")
    preprocess_out = _preprocessing.process({
        "image_bytes": image_bytes,
        "filename": filename,
    })

    # ── Stage 2: Embedding (pHash) ────────────────────────────────
    ctx.info("pipeline.embedding")
    embedding_out = _embedding.process({
        "image": preprocess_out["image"],
    })

    # ── Stage 3: Matching (Hamming Distance) ──────────────────────
    ctx.info("pipeline.matching")
    matching_out = _matching.process({
        "phash": embedding_out["phash"],
    })

    candidates = matching_out["candidates"]

    # ── Stage 4: Risk ─────────────────────────────────────────────
    ctx.info("pipeline.risk")
    risk_out = _risk.process({
        "candidates": candidates,
    })

    # ── Stage 5: Decision ─────────────────────────────────────────
    ctx.info("pipeline.decision")
    decision_out = _decision.process({
        "risk_score": risk_out["risk_score"],
        "signals": risk_out["signals"],
    })

    # ── Stage 6: Explainability ───────────────────────────────────
    ctx.info("pipeline.explainability")
    explain_out = _explainability.process({
        "risk_score": risk_out["risk_score"],
        "signals": risk_out["signals"],
        "candidates": candidates,
        "decision": decision_out["decision"],
    })

    ctx.info(
        "pipeline.complete",
        decision=decision_out["decision"],
        risk_score=risk_out["risk_score"],
        num_candidates=len(candidates),
    )

    return {
        "trace_id": trace_id,
        "asset_id": asset_id,
        "risk_score": risk_out["risk_score"],
        "decision": decision_out["decision"],
        "signals": risk_out["signals"],
        "explanation": explain_out["explanation"],
        "matches": candidates,
        "phash": embedding_out["phash"],
        "model_version": settings.MODEL_VERSION,
        "index_version": settings.INDEX_VERSION,
        "policy_version": settings.POLICY_VERSION,
    }
