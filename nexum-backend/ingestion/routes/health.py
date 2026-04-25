"""NEXUM SHIELD — Ingestion API: Health Check"""
from fastapi import APIRouter
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "nexum-ingestion",
        "bucket": settings.GCS_BUCKET,
        "topic": settings.PUBSUB_TOPIC,
    }
