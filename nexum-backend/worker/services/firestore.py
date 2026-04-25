import os
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

# Local mock storage files
STORAGE_DIR = Path("C:/tmp/nexum-storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def _load(collection: str) -> dict:
    p = STORAGE_DIR / f"{collection}.json"
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    return {}

def _save(collection: str, data: dict) -> None:
    with open(STORAGE_DIR / f"{collection}.json", "w") as f:
        json.dump(data, f)

async def create_asset_record(
    asset_id: str,
    trace_id: str,
    gcs_path: str,
    phash: str,
    source: str,
) -> None:
    """Mock write initial asset record."""
    data = _load("assets")
    data[asset_id] = {
        "asset_id": asset_id,
        "trace_id": trace_id,
        "gcs_path": gcs_path,
        "phash": phash,
        "source": source,
        "status": "processing",
        "created_at": datetime.utcnow().isoformat(),
    }
    _save("assets", data)

async def update_asset_status(asset_id: str, status: str) -> None:
    """Mock update asset processing status."""
    data = _load("assets")
    if asset_id in data:
        data[asset_id]["status"] = status
        data[asset_id]["updated_at"] = datetime.utcnow().isoformat()
        _save("assets", data)

async def write_decision(decision_data: dict[str, Any]) -> None:
    """Mock write decision record."""
    data = _load("decisions")
    trace_id = decision_data["trace_id"]
    doc = {**decision_data}
    if "matches" in doc:
        doc["matches"] = [{"id": m["id"], "score": m["score"]} for m in doc["matches"]]
    data[trace_id] = doc
    _save("decisions", data)

async def get_decision(trace_id: str) -> Optional[dict[str, Any]]:
    """Mock retrieve decision."""
    return _load("decisions").get(trace_id)

async def get_asset(asset_id: str) -> Optional[dict[str, Any]]:
    """Mock retrieve asset."""
    return _load("assets").get(asset_id)

async def get_decision_by_asset(asset_id: str) -> Optional[dict[str, Any]]:
    """Mock find decision by asset_id."""
    docs = _load("decisions").values()
    for d in docs:
        if d.get("asset_id") == asset_id:
            return d
    return None

async def list_decisions(limit: int = 50) -> list[dict[str, Any]]:
    """Mock list recent decisions."""
    docs = list(_load("decisions").values())
    docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return docs[:limit]

async def add_known_asset(asset_id: str, name: str, gcs_path: str, faiss_index: int) -> None:
    """Mock register known asset."""
    data = _load("known_assets")
    data[asset_id] = {
        "id": asset_id,
        "name": name,
        "gcs_path": gcs_path,
        "faiss_index": faiss_index,
        "created_at": datetime.utcnow().isoformat(),
    }
    _save("known_assets", data)
