"""
NEXUM SHIELD — Firestore Service (Worker)
Auto-detects: uses local JSON files in dev, real Firestore in Cloud Run.
"""
import os
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

LOCAL_STORAGE = Path("C:/tmp/nexum-storage")
LOCAL_STORAGE.mkdir(parents=True, exist_ok=True)


def _use_local() -> bool:
    from config import settings
    return not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not settings.USE_FIRESTORE_EMULATOR


# ─── Local File I/O ───────────────────────────────────────────────
def _load(collection: str) -> dict:
    p = LOCAL_STORAGE / f"{collection}.json"
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    return {}

def _save(collection: str, data: dict) -> None:
    with open(LOCAL_STORAGE / f"{collection}.json", "w") as f:
        json.dump(data, f)


# ─── Real Firestore ───────────────────────────────────────────────
def _get_client():
    from google.cloud import firestore
    from google.auth.credentials import AnonymousCredentials
    from config import settings
    if settings.USE_FIRESTORE_EMULATOR:
        os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
        return firestore.Client(project=settings.GCP_PROJECT_ID, credentials=AnonymousCredentials())
    return firestore.Client(project=settings.GCP_PROJECT_ID)


# ─── Service Methods ──────────────────────────────────────────────
async def create_asset_record(asset_id: str, trace_id: str, gcs_path: str, phash: str, source: str) -> None:
    record = {"asset_id": asset_id, "trace_id": trace_id, "gcs_path": gcs_path,
              "phash": phash, "source": source, "status": "processing",
              "created_at": datetime.utcnow().isoformat()}
    if _use_local():
        data = _load("assets"); data[asset_id] = record; _save("assets", data)
    else:
        _get_client().collection("assets").document(asset_id).set(record)


async def update_asset_status(asset_id: str, status: str) -> None:
    update = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    if _use_local():
        data = _load("assets")
        if asset_id in data:
            data[asset_id].update(update); _save("assets", data)
    else:
        _get_client().collection("assets").document(asset_id).update(update)


async def write_decision(decision_data: dict[str, Any]) -> None:
    doc = {**decision_data}
    if "matches" in doc:
        doc["matches"] = [{"id": m["id"], "score": m["score"]} for m in doc["matches"]]
    trace_id = doc["trace_id"]
    if _use_local():
        data = _load("decisions"); data[trace_id] = doc; _save("decisions", data)
    else:
        _get_client().collection("decisions").document(trace_id).set(doc)


async def get_decision(trace_id: str) -> Optional[dict[str, Any]]:
    if _use_local():
        return _load("decisions").get(trace_id)
    doc = _get_client().collection("decisions").document(trace_id).get()
    return doc.to_dict() if doc.exists else None


async def get_asset(asset_id: str) -> Optional[dict[str, Any]]:
    if _use_local():
        return _load("assets").get(asset_id)
    doc = _get_client().collection("assets").document(asset_id).get()
    return doc.to_dict() if doc.exists else None


async def get_decision_by_asset(asset_id: str) -> Optional[dict[str, Any]]:
    if _use_local():
        for d in _load("decisions").values():
            if d.get("asset_id") == asset_id:
                return d
        return None
    from google.cloud import firestore
    docs = list(_get_client().collection("decisions").where("asset_id", "==", asset_id).limit(1).stream())
    return docs[0].to_dict() if docs else None


async def list_decisions(limit: int = 50) -> list[dict[str, Any]]:
    if _use_local():
        docs = list(_load("decisions").values())
        docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return docs[:limit]
    from google.cloud import firestore
    query = _get_client().collection("decisions").order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
    return [doc.to_dict() for doc in query.stream()]


async def add_known_asset(asset_id: str, name: str, gcs_path: str, faiss_index: int) -> None:
    record = {"id": asset_id, "name": name, "gcs_path": gcs_path,
              "faiss_index": faiss_index, "created_at": datetime.utcnow().isoformat()}
    if _use_local():
        data = _load("known_assets"); data[asset_id] = record; _save("known_assets", data)
    else:
        _get_client().collection("known_assets").document(asset_id).set(record)
