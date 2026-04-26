"""
NEXUM SHIELD — GCS Service (Worker)
Handles downloading images and uploading/downloading the pHash index.
Supports real GCS for Cloud Run deployment and local filesystem for dev.
"""
import os
import shutil
from pathlib import Path

from config import settings

# ─── Local dev storage directory ─────────────────────────────────
LOCAL_STORAGE = Path("C:/tmp/nexum-storage")


def _use_local() -> bool:
    """Return True if we are running locally without real GCS credentials."""
    return not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not settings.USE_GCS_EMULATOR


def _get_client():
    from google.cloud import storage
    from google.auth.credentials import AnonymousCredentials
    if settings.USE_GCS_EMULATOR:
        os.environ["STORAGE_EMULATOR_HOST"] = settings.GCS_EMULATOR_HOST
        return storage.Client(
            project=settings.GCP_PROJECT_ID,
            credentials=AnonymousCredentials(),
        )
    return storage.Client(project=settings.GCP_PROJECT_ID)


def download_file(gcs_path: str, local_path: str) -> None:
    """Download from GCS (real) or local mirror in dev mode."""
    if _use_local():
        blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
        src = LOCAL_STORAGE / blob_name
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, local_path)
        return

    client = _get_client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
    blob = bucket.blob(blob_name)
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(local_path)


def upload_file(local_path: str, gcs_path: str) -> None:
    """Upload to GCS (real) or local mirror in dev mode."""
    if _use_local():
        blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
        dest = LOCAL_STORAGE / blob_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, dest)
        return

    client = _get_client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)


def download_index() -> bool:
    """
    Download pHash index from GCS (or local mirror).
    Returns True if found, False if fresh deploy.
    """
    try:
        download_file(settings.FAISS_INDEX_GCS_PATH, settings.FAISS_LOCAL_PATH)
        return os.path.exists(settings.FAISS_LOCAL_PATH)
    except Exception:
        for path in [settings.FAISS_LOCAL_PATH, settings.FAISS_ID_MAP_LOCAL_PATH]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        return False


def upload_index() -> None:
    """Upload pHash index back to GCS (or local mirror)."""
    upload_file(settings.FAISS_LOCAL_PATH, settings.FAISS_INDEX_GCS_PATH)


def download_asset(gcs_path: str, local_path: str) -> None:
    """Download a media asset for processing."""
    download_file(gcs_path, local_path)


def ensure_bucket_exists() -> None:
    """Create local dev storage dir or GCS bucket."""
    if _use_local():
        LOCAL_STORAGE.mkdir(parents=True, exist_ok=True)
        return
    try:
        client = _get_client()
        bucket = client.bucket(settings.GCS_BUCKET)
        if not bucket.exists():
            bucket.create(location="us-central1")
    except Exception:
        pass
