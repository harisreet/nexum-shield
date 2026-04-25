"""
NEXUM SHIELD — Ingestion API: GCS Service
Uploads raw media assets to Cloud Storage.
"""
import os
import uuid
from pathlib import Path

from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

from config import settings


def _get_client() -> storage.Client:
    pass

def ensure_bucket() -> None:
    """Create bucket if it doesn't exist (local dev only)."""
    Path("C:/tmp/nexum-storage/uploads").mkdir(parents=True, exist_ok=True)

def upload_asset(file_bytes: bytes, asset_id: str, content_type: str) -> str:
    """
    Upload raw media bytes to GCS under uploads/{asset_id}.
    Returns the full GCS path: gs://bucket/uploads/asset_id.ext
    """
    ext = _ext_from_content_type(content_type)
    blob_name = f"uploads/{asset_id}{ext}"
    
    local_path = f"C:/tmp/nexum-storage/{blob_name}"
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    return f"gs://{settings.GCS_BUCKET}/{blob_name}"


def _ext_from_content_type(ct: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return mapping.get(ct, ".jpg")
