"""
NEXUM SHIELD — Ingestion API: Upload Route
Validates the file, stores in GCS, fires a Pub/Sub event.
No analysis happens here — this service is thin by design.
"""
import uuid

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

import structlog

from config import settings
from schemas import UploadResponse
from services import pubsub as pubsub_service

log = structlog.get_logger()
router = APIRouter(tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload", response_model=UploadResponse)
async def upload_asset(
    file: UploadFile = File(..., description="Image file to analyze (JPEG, PNG, WEBP)"),
    source: str = Form(default="api", description="Source system identifier"),
):
    """
    Accept an image upload, store in GCS, publish event to Pub/Sub.
    Returns asset_id and trace_id for polling.
    """
    asset_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    ctx = log.bind(asset_id=asset_id, trace_id=trace_id)

    # ── Validate content type ─────────────────────────────────────
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: {sorted(ALLOWED_TYPES)}",
        )

    # ── Read and size-check ───────────────────────────────────────
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {size_mb:.1f}MB. Max: {settings.MAX_FILE_SIZE_MB}MB",
        )

    ctx.info("upload.storing", size_mb=round(size_mb, 2), content_type=content_type)

    # ── Upload to Worker via HTTP (No GCS needed!) ────────────────
    try:
        message_id = pubsub_service.publish_media_event(
            asset_id=asset_id,
            trace_id=trace_id,
            file_bytes=file_bytes,
            source=source,
        )
    except Exception as e:
        ctx.error("upload.pubsub_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Event publishing error: {e}")

    ctx.info("upload.published", message_id=message_id)

    return UploadResponse(
        asset_id=asset_id,
        trace_id=trace_id,
        status="processing",
        message="Asset received. Processing pipeline started.",
    )
