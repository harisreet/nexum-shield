"""
NEXUM SHIELD — Ingestion API: Pub/Sub Service
Publishes media-ready events to the Pub/Sub topic.
"""
import json
import os
import base64
from datetime import datetime

from google.cloud import pubsub_v1
from google.auth.credentials import AnonymousCredentials
from google.api_core.exceptions import GoogleAPICallError

from config import settings


def _get_publisher() -> None:
    pass

def publish_media_event(
    asset_id: str,
    trace_id: str,
    gcs_path: str,
    source: str = "api",
) -> str:
    """Mock publish: HTTP POST directly to worker on localhost:8002."""
    import requests
    
    payload = {
        "trace_id": trace_id,
        "asset_id": asset_id,
        "gcs_path": gcs_path,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }
    data = json.dumps(payload).encode("utf-8")
    b64_data = base64.b64encode(data).decode('utf-8')
    
    message = {
        "message": {
            "data": b64_data
        }
    }
    
    try:
        # Start worker processing via HTTP Push
        res = requests.post("http://localhost:8002/process", json=message, timeout=30)
        res.raise_for_status()
        return "mock-msg-" + asset_id
    except Exception as e:
        raise RuntimeError(f"Mock Pub/Sub publish failed: {e}") from e
