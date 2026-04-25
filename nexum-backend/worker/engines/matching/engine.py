"""
NEXUM SHIELD — Matching Engine (FAISS)
Performs top-K cosine similarity search against the known asset index.
Index is loaded once at startup from disk (downloaded from GCS by services/gcs.py).
"""
import json
import os
from typing import Any

import faiss
import numpy as np

from config import settings
from engines.base import Engine, EngineError

# ─── Singleton index state ────────────────────────────────────────
_index: faiss.Index | None = None
_id_map: dict[int, str] = {}   # faiss internal int → asset UUID


def load_faiss_index() -> None:
    """Load FAISS index + ID map from disk. Called once at app startup."""
    global _index, _id_map

    index_path = settings.FAISS_LOCAL_PATH
    id_map_path = settings.FAISS_ID_MAP_LOCAL_PATH

    if os.path.exists(index_path):
        try:
            _index = faiss.read_index(index_path)
        except Exception as e:
            # Corrupt file (empty download, partial write, etc.) — start fresh
            print(f"[MatchingEngine] Corrupt FAISS index ({e}). Deleting and bootstrapping empty index.")
            os.remove(index_path)
            if os.path.exists(id_map_path):
                os.remove(id_map_path)
            _index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)
    else:
        # Bootstrap empty index — ready for seeding
        _index = faiss.IndexFlatIP(settings.EMBEDDING_DIM)

    if os.path.exists(id_map_path):
        try:
            with open(id_map_path, "r") as f:
                raw = json.load(f)
                _id_map = {int(k): v for k, v in raw.items()}
        except Exception:
            _id_map = {}
    else:
        _id_map = {}


def save_faiss_index() -> None:
    """Persist index + ID map to disk (called after seeding)."""
    if _index is None:
        return
    faiss.write_index(_index, settings.FAISS_LOCAL_PATH)
    with open(settings.FAISS_ID_MAP_LOCAL_PATH, "w") as f:
        json.dump(_id_map, f)


def add_to_index(vector: list[float], asset_id: str) -> int:
    """
    Add a vector to the index.
    Returns the FAISS internal integer ID.
    Thread-unsafe — caller must serialize writes.
    """
    global _index, _id_map
    if _index is None:
        load_faiss_index()

    vec = np.array([vector], dtype=np.float32)
    faiss_id = _index.ntotal
    _index.add(vec)
    _id_map[faiss_id] = asset_id
    return faiss_id


def get_index_size() -> int:
    return _index.ntotal if _index else 0


class MatchingEngine(Engine):
    """
    Input:  { "vector": list[float] }
    Output: { "candidates": [{"id": str, "score": float}], "index_version": str }

    Uses IndexFlatIP (inner product). Because vectors are L2-normalized in
    EmbeddingEngine, IP == cosine similarity. Scores are in [-1, 1].
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        vector: list[float] | None = input_data.get("vector")
        if vector is None:
            raise EngineError(self.name, "No vector provided.")

        if _index is None:
            raise EngineError(self.name, "FAISS index not loaded. Call load_faiss_index() at startup.")

        # Empty index → no candidates, risk = 0
        if _index.ntotal == 0:
            return {
                "candidates": [],
                "index_version": settings.INDEX_VERSION,
            }

        query = np.array([vector], dtype=np.float32)
        k = min(settings.TOP_K, _index.ntotal)

        try:
            scores, indices = _index.search(query, k)
        except Exception as e:
            raise EngineError(self.name, f"FAISS search failed: {e}", original=e)

        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            asset_id = _id_map.get(int(idx), f"unknown:{idx}")
            candidates.append({
                "id": asset_id,
                "score": float(score),
            })

        return {
            "candidates": sorted(candidates, key=lambda c: c["score"], reverse=True),
            "index_version": settings.INDEX_VERSION,
        }
