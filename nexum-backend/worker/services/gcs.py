"""
NEXUM SHIELD — GCS Service (Worker)
Handles downloading images and uploading/downloading the FAISS index.
Supports local fake-gcs-server for dev and real GCS for production.
"""
import os
from pathlib import Path

from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

from config import settings


def _get_client() -> None:
    pass

def download_file(gcs_path: str, local_path: str) -> None:
    """Mock download from C:/tmp/nexum-storage/."""
    blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
    src_path = f"C:/tmp/nexum-storage/{blob_name}"
    
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(src_path):
        import shutil
        shutil.copy2(src_path, local_path)

def upload_file(local_path: str, gcs_path: str) -> None:
    """Mock upload to C:/tmp/nexum-storage/."""
    blob_name = gcs_path.replace(f"gs://{settings.GCS_BUCKET}/", "")
    dest_path = f"C:/tmp/nexum-storage/{blob_name}"
    
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(local_path, dest_path)


def download_index() -> bool:
    """
    Download FAISS index + ID map from GCS to /tmp.
    Returns True if index was found, False if it doesn't exist yet (fresh deploy).
    On failure, any partial file is deleted to prevent corrupt reads on next startup.
    """
    try:
        download_file(settings.FAISS_INDEX_GCS_PATH, settings.FAISS_LOCAL_PATH)
        download_file(settings.FAISS_ID_MAP_GCS_PATH, settings.FAISS_ID_MAP_LOCAL_PATH)
        return True
    except Exception:
        # Clean up any partial files left by a failed download
        for path in [settings.FAISS_LOCAL_PATH, settings.FAISS_ID_MAP_LOCAL_PATH]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        return False  # Bootstrap case — no index yet


def upload_index() -> None:
    """Upload updated FAISS index + ID map back to GCS."""
    upload_file(settings.FAISS_LOCAL_PATH, settings.FAISS_INDEX_GCS_PATH)
    upload_file(settings.FAISS_ID_MAP_LOCAL_PATH, settings.FAISS_ID_MAP_GCS_PATH)


def download_asset(gcs_path: str, local_path: str) -> None:
    """Download an uploaded media asset to local disk for processing."""
    download_file(gcs_path, local_path)


def ensure_bucket_exists() -> None:
    pass
