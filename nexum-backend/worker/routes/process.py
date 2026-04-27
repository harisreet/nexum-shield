"""
NEXUM SHIELD — Worker: Pub/Sub Push Handler
Receives push messages from Pub/Sub, downloads image from GCS,
runs the full pipeline, writes results to Firestore.
Returns 200 to ACK the message. Returns 4xx to NACK (retry).
"""
import base64
import json
import uuid
import tempfile
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

import structlog

from schemas import PubSubPushRequest, PubSubEvent
from pipeline import run_pipeline
from services import firestore as fs_service
from engines.base import EngineError

log = structlog.get_logger()
router = APIRouter()


@router.post("/process", status_code=200)
async def process_event(request: PubSubPushRequest, background: BackgroundTasks):
    """
    Pub/Sub push endpoint.
    Pub/Sub expects HTTP 200–299 to ACK.
    Any other status triggers retry with exponential backoff.
    """
    trace_id = str(uuid.uuid4())

    # ── Decode Pub/Sub message ────────────────────────────────────
    try:
        raw_data = base64.b64decode(request.message.data).decode("utf-8")
        event = PubSubEvent(**json.loads(raw_data))
    except Exception as e:
        log.error("process.decode_failed", error=str(e))
        # Return 200 to ACK bad message (prevents infinite retry loop)
        return JSONResponse({"error": "invalid_message", "detail": str(e)}, status_code=200)

    ctx = log.bind(trace_id=trace_id, asset_id=event.asset_id)
    ctx.info("process.received")

    # ── Decode image bytes directly from payload (No GCS needed!) ─
    try:
        image_bytes = base64.b64decode(event.image_b64)
    except Exception as e:
        ctx.error("process.image_decode_failed", error=str(e))
        return JSONResponse({"error": "invalid_image_encoding"}, status_code=200)

    # ── Mark asset as processing ──────────────────────────────────
    try:
        await fs_service.create_asset_record(
            asset_id=event.asset_id,
            trace_id=trace_id,
            gcs_path="",  # Deprecated
            phash="",  # will be updated after preprocessing
            source=event.source,
        )
    except Exception as e:
        ctx.warning("process.firestore_asset_create_failed", error=str(e))

    # ── Run pipeline ──────────────────────────────────────────────
    try:
        result = await run_pipeline(
            image_bytes=image_bytes,
            filename="upload.jpg",
            asset_id=event.asset_id,
            trace_id=trace_id,
        )
    except EngineError as e:
        ctx.error("process.pipeline_failed", engine=e.engine, error=str(e))
        await fs_service.update_asset_status(event.asset_id, "error")
        # Return 200 to ACK — pipeline error is not a delivery issue
        return JSONResponse({"error": "pipeline_failed", "engine": e.engine}, status_code=200)
    except Exception as e:
        ctx.error("process.unexpected_error", error=str(e))
        await fs_service.update_asset_status(event.asset_id, "error")
        return JSONResponse({"error": "unexpected_error"}, status_code=200)

    # ── Persist decision ──────────────────────────────────────────
    decision_record = {
        "trace_id": trace_id,
        "asset_id": event.asset_id,
        "risk_score": result["risk_score"],
        "decision": result["decision"],
        "signals": result["signals"],
        "explanation": result["explanation"],
        "matches": result["matches"],
        "model_version": result["model_version"],
        "index_version": result["index_version"],
        "policy_version": result["policy_version"],
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        await fs_service.write_decision(decision_record)
        await fs_service.update_asset_status(event.asset_id, "complete")
    except Exception as e:
        ctx.error("process.firestore_write_failed", error=str(e))

    ctx.info(
        "process.complete",
        decision=result["decision"],
        risk_score=result["risk_score"],
    )

    return {"status": "ok", "trace_id": trace_id, "decision": result["decision"]}
