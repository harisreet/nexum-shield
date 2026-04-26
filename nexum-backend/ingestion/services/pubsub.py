"""
NEXUM SHIELD — Ingestion API: Pub/Sub Service
Auto-detects: direct HTTP POST to worker in dev, real Pub/Sub on Cloud Run.
"""
import json
import os
import base64
from datetime import datetime

from config import settings


def _use_local() -> bool:
    return not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not settings.USE_PUBSUB_EMULATOR


def publish_media_event(asset_id: str, trace_id: str, gcs_path: str, source: str = "api") -> str:
    payload = {
        "trace_id": trace_id, "asset_id": asset_id,
        "gcs_path": gcs_path, "source": source,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if _use_local():
        # Dev mode: direct HTTP POST to worker
        import requests
        data = json.dumps(payload).encode("utf-8")
        b64_data = base64.b64encode(data).decode("utf-8")
        try:
            res = requests.post(
                "http://localhost:8002/process",
                json={"message": {"data": b64_data}},
                timeout=30,
            )
            res.raise_for_status()
            return "local-msg-" + asset_id
        except Exception as e:
            raise RuntimeError(f"Worker call failed: {e}") from e

    # Cloud Run mode: real Pub/Sub
    from google.cloud import pubsub_v1
    if settings.USE_PUBSUB_EMULATOR:
        os.environ["PUBSUB_EMULATOR_HOST"] = settings.PUBSUB_EMULATOR_HOST
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(settings.GCP_PROJECT_ID, settings.PUBSUB_TOPIC)
    data = json.dumps(payload).encode("utf-8")
    try:
        future = publisher.publish(topic_path, data=data)
        return future.result(timeout=10)
    except Exception as e:
        raise RuntimeError(f"Pub/Sub publish failed: {e}") from e
