"""
NEXUM SHIELD — Ingestion API: Pub/Sub Service
Uses WORKER_URL env var for Railway/production, falls back to localhost for dev.
Sends the image bytes directly in the JSON payload (base64 encoded).
"""
import json
import base64
from datetime import datetime

import requests

from config import settings


def publish_media_event(asset_id: str, trace_id: str, file_bytes: bytes, source: str = "api") -> str:
    """
    Forward media event directly to the Worker via HTTP POST.
    Includes the actual image bytes in base64 format.
    """
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")
    
    payload = {
        "trace_id": trace_id,
        "asset_id": asset_id,
        "image_b64": image_b64,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # We double-encode because the Worker currently expects a Pub/Sub emulator format
    # where the whole payload is inside `message.data` as base64.
    data_str = json.dumps(payload).encode("utf-8")
    pubsub_b64 = base64.b64encode(data_str).decode("utf-8")

    worker_url = settings.WORKER_URL.rstrip("/") + "/process"

    try:
        res = requests.post(
            worker_url,
            json={"message": {"data": pubsub_b64}},
            timeout=30,
        )
        res.raise_for_status()
        return "msg-" + asset_id
    except Exception as e:
        raise RuntimeError(f"Worker call failed ({worker_url}): {e}") from e
