"""NEXUM SHIELD — Worker: Health Check"""
from fastapi import APIRouter
from engines.matching.engine import get_index_size
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "nexum-worker",
        "index_size": get_index_size(),
        "model_version": settings.MODEL_VERSION,
        "index_version": settings.INDEX_VERSION,
        "policy_version": settings.POLICY_VERSION,
    }
