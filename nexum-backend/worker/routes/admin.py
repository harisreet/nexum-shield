"""
NEXUM SHIELD — Worker: Admin Routes (pHash Edition)
Seed endpoint, index stats, result polling, audit log.
"""
import uuid
import io
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

import structlog

from config import settings
from engines.preprocessing.processor import PreprocessingEngine
from engines.embedding.engine import EmbeddingEngine
from engines.matching.engine import add_to_index, get_index_size, save_faiss_index
from services import firestore as fs_service
from schemas import IndexStats, SeedResponse

log = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])

_preprocessor = PreprocessingEngine()
_embedder = EmbeddingEngine()


# ─── Index Stats ──────────────────────────────────────────────────

@router.get("/index-stats", response_model=IndexStats)
async def get_index_stats():
    """Return current pHash index size and version info."""
    return IndexStats(
        total_vectors=get_index_size(),
        index_version=settings.INDEX_VERSION,
        model_version=settings.MODEL_VERSION,
        index_on_disk=True,
    )


# ─── Seed Known Asset ─────────────────────────────────────────────

@router.post("/seed", response_model=SeedResponse)
async def seed_asset(
    file: UploadFile = File(...),
    name: str = Query(default="", description="Human-readable name for this reference asset"),
):
    """
    Add an image to the known reference dataset.
    Preprocesses the image, computes its pHash, and adds it to the
    in-memory index. Persists the index to GCS for durability.
    """
    asset_id = str(uuid.uuid4())
    image_bytes = await file.read()

    # ── Preprocess ────────────────────────────────────────────────
    try:
        preprocess_out = _preprocessor.process({
            "image_bytes": image_bytes,
            "filename": file.filename or "seed.jpg",
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing failed: {e}")

    # ── Compute pHash ─────────────────────────────────────────────
    try:
        embedding_out = _embedder.process({"image": preprocess_out["image"]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"pHash generation failed: {e}")

    # ── Add to pHash index ────────────────────────────────────────
    new_size = add_to_index(embedding_out["phash"], asset_id)

    # ── Persist index to MongoDB/Disk ─────────────────────────────
    save_faiss_index()

    # ── Register in MongoDB/Firestore ─────────────────────────────
    try:
        await fs_service.add_known_asset(
            asset_id=asset_id,
            name=name or file.filename or asset_id,
            gcs_path="none",  # GCS removed
            faiss_index=new_size,
        )
    except Exception as e:
        log.warning("seed.firestore_failed", error=str(e))

    log.info("seed.complete", asset_id=asset_id, phash=embedding_out["phash"], total=new_size)

    return SeedResponse(
        asset_id=asset_id,
        message=f"Asset seeded successfully. Index now has {new_size} assets.",
    )


# ─── Result Polling ───────────────────────────────────────────────

@router.get("/result")
async def get_result(asset_id: str = Query(..., description="Asset ID returned from /upload")):
    """
    Poll for decision result by asset_id.
    Returns status=processing if pipeline is still running.
    """
    asset = await fs_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")

    if asset.get("status") != "complete":
        return {"status": asset.get("status", "processing"), "asset_id": asset_id}

    decision = await fs_service.get_decision_by_asset(asset_id)
    if not decision:
        return {"status": "processing", "asset_id": asset_id}

    return {"status": "complete", **decision}


# ─── Audit Log ────────────────────────────────────────────────────

@router.get("/decisions")
async def list_decisions(limit: int = Query(default=50, le=200)):
    """Return paginated audit log of all decisions."""
    decisions = await fs_service.list_decisions(limit=limit)
    return {"decisions": decisions, "count": len(decisions)}
