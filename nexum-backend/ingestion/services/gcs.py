"""
NEXUM SHIELD — Ingestion API: GCS Service
Uploads raw media assets to Cloud Storage.
Auto-detects local dev vs real GCS based on credentials.
"""
import os
import shutil
from pathlib import Path

from config import settings

LOCAL_STORAGE = Path("C:/tmp/nexum-storage")


def _use_local() -> bool:
    return not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not settings.USE_GCS_EMULATOR


def _get_client():
    from google.cloud import storage
    from google.auth.credentials import AnonymousCredentials
    if settings.USE_GCS_EMULATOR:
        os.environ["STORAGE_EMULATOR_HOST"] = settings.GCS_EMULATOR_HOST
        return storage.Client(project=settings.GCP_PROJECT_ID, credentials=AnonymousCredentials())
    return storage.Client(project=settings.GCP_PROJECT_ID)


def ensure_bucket() -> None:
    if _use_local():
        (LOCAL_STORAGE / "uploads").mkdir(parents=True, exist_ok=True)
        return
    try:
        client = _get_client()
        bucket = client.bucket(settings.GCS_BUCKET)
        if not bucket.exists():
            bucket.create(location="us-central1")
    except Exception:
        pass


def upload_asset(file_bytes: bytes, asset_id: str, content_type: str) -> str:
    """Upload raw media bytes. Returns GCS path."""
    ext = _ext_from_content_type(content_type)
    blob_name = f"uploads/{asset_id}{ext}"

    if _use_local():
        dest = LOCAL_STORAGE / blob_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(file_bytes)
        return f"gs://{settings.GCS_BUCKET}/{blob_name}"

    client = _get_client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type=content_type)
    return f"gs://{settings.GCS_BUCKET}/{blob_name}"


def _ext_from_content_type(ct: str) -> str:
    return {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(ct, ".jpg")
