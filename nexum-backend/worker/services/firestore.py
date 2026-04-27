"""
NEXUM SHIELD — Firestore Service (Worker)
Auto-detects storage backend:
  - MongoDB Atlas if MONGODB_URI is set (Railway/production)
  - Local JSON files if no MONGODB_URI (dev mode)
"""
import os
import json
from datetime import datetime
from typing import Any, Optional
from pathlib import Path

LOCAL_STORAGE = Path(os.environ.get("LOCAL_STORAGE_PATH", "C:/tmp/nexum-storage"))
LOCAL_STORAGE.mkdir(parents=True, exist_ok=True)


def _mongo_uri() -> str:
    from config import settings
    return getattr(settings, "MONGODB_URI", "")


def _use_mongo() -> bool:
    return bool(_mongo_uri())


def _get_db():
    """Get MongoDB database instance."""
    from pymongo import MongoClient
    client = MongoClient(_mongo_uri(), serverSelectionTimeoutMS=5000)
    return client["nexum"]


# ─── Local JSON helpers ───────────────────────────────────────────
def _load(collection: str) -> dict:
    p = LOCAL_STORAGE / f"{collection}.json"
    if p.exists():
        with open(p, "r") as f:
            return json.load(f)
    return {}


def _save(collection: str, data: dict) -> None:
    with open(LOCAL_STORAGE / f"{collection}.json", "w") as f:
        json.dump(data, f)


# ─── Service Methods ──────────────────────────────────────────────
async def create_asset_record(asset_id: str, trace_id: str, gcs_path: str, phash: str, source: str) -> None:
    record = {
        "asset_id": asset_id, "trace_id": trace_id, "gcs_path": gcs_path,
        "phash": phash, "source": source, "status": "processing",
        "created_at": datetime.utcnow().isoformat(),
    }
    if _use_mongo():
        _get_db()["assets"].replace_one({"asset_id": asset_id}, record, upsert=True)
    else:
        data = _load("assets"); data[asset_id] = record; _save("assets", data)


async def update_asset_status(asset_id: str, status: str) -> None:
    update = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    if _use_mongo():
        _get_db()["assets"].update_one({"asset_id": asset_id}, {"$set": update})
    else:
        data = _load("assets")
        if asset_id in data:
            data[asset_id].update(update); _save("assets", data)


async def write_decision(decision_data: dict[str, Any]) -> None:
    doc = {**decision_data}
    if "matches" in doc:
        doc["matches"] = [{"id": m["id"], "score": m["score"]} for m in doc["matches"]]
    if _use_mongo():
        _get_db()["decisions"].replace_one({"trace_id": doc["trace_id"]}, doc, upsert=True)
    else:
        data = _load("decisions"); data[doc["trace_id"]] = doc; _save("decisions", data)


async def get_decision(trace_id: str) -> Optional[dict[str, Any]]:
    if _use_mongo():
        doc = _get_db()["decisions"].find_one({"trace_id": trace_id}, {"_id": 0})
        return doc
    return _load("decisions").get(trace_id)


async def get_asset(asset_id: str) -> Optional[dict[str, Any]]:
    if _use_mongo():
        doc = _get_db()["assets"].find_one({"asset_id": asset_id}, {"_id": 0})
        return doc
    return _load("assets").get(asset_id)


async def get_decision_by_asset(asset_id: str) -> Optional[dict[str, Any]]:
    if _use_mongo():
        doc = _get_db()["decisions"].find_one({"asset_id": asset_id}, {"_id": 0})
        return doc
    for d in _load("decisions").values():
        if d.get("asset_id") == asset_id:
            return d
    return None


async def list_decisions(limit: int = 50) -> list[dict[str, Any]]:
    if _use_mongo():
        cursor = _get_db()["decisions"].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)
    docs = list(_load("decisions").values())
    docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return docs[:limit]


async def add_known_asset(asset_id: str, name: str, gcs_path: str, faiss_index: int) -> None:
    record = {
        "id": asset_id, "name": name, "gcs_path": gcs_path,
        "faiss_index": faiss_index, "created_at": datetime.utcnow().isoformat(),
    }
    if _use_mongo():
        _get_db()["known_assets"].replace_one({"id": asset_id}, record, upsert=True)
    else:
        data = _load("known_assets"); data[asset_id] = record; _save("known_assets", data)
