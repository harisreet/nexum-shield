"""
NEXUM SHIELD — Matching Engine (pHash Hamming Distance)
Replaces FAISS vector search with perceptual hash comparison.
Stores known asset pHashes in a simple in-memory dict (persisted to JSON).
"""
import json
import os
from typing import Any

import imagehash

from config import settings
from engines.base import Engine, EngineError

# ─── Singleton index state ────────────────────────────────────────
# Maps asset_id → phash string
_phash_index: dict[str, str] = {}

# Max hamming distance to consider a match (out of 64 bits)
# 10/64 bits different = ~84% similar = strong match
HAMMING_THRESHOLD = 10


def load_faiss_index() -> None:
    """Load pHash index from disk. Called once at startup."""
    global _phash_index

    index_path = settings.FAISS_LOCAL_PATH  # reuse the same config path
    if os.path.exists(index_path):
        try:
            with open(index_path, "r") as f:
                _phash_index = json.load(f)
            print(f"[MatchingEngine] Loaded pHash index with {len(_phash_index)} assets.")
        except Exception as e:
            print(f"[MatchingEngine] Failed to load pHash index ({e}). Starting fresh.")
            _phash_index = {}
    else:
        _phash_index = {}
        print("[MatchingEngine] No pHash index found. Starting fresh.")


def save_faiss_index() -> None:
    """Persist pHash index to disk."""
    os.makedirs(os.path.dirname(settings.FAISS_LOCAL_PATH), exist_ok=True)
    with open(settings.FAISS_LOCAL_PATH, "w") as f:
        json.dump(_phash_index, f)


def add_to_index(phash: str, asset_id: str) -> int:
    """
    Add a pHash to the index.
    Returns the new index size.
    """
    _phash_index[asset_id] = phash
    return len(_phash_index)


def get_index_size() -> int:
    return len(_phash_index)


class MatchingEngine(Engine):
    """
    Input:  { "phash": str }
    Output: { "candidates": [{"id": str, "score": float}], "index_version": str }

    Computes Hamming distance between query pHash and all known pHashes.
    Score is normalized: 1.0 = identical, 0.0 = completely different.
    """

    def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query_phash_str: str | None = input_data.get("phash")
        if query_phash_str is None:
            raise EngineError(self.name, "No phash provided.")

        if not _phash_index:
            return {
                "candidates": [],
                "index_version": settings.INDEX_VERSION,
            }

        try:
            query_hash = imagehash.hex_to_hash(query_phash_str)
        except Exception as e:
            raise EngineError(self.name, f"Invalid pHash string: {e}", original=e)

        candidates = []
        for asset_id, stored_phash_str in _phash_index.items():
            try:
                stored_hash = imagehash.hex_to_hash(stored_phash_str)
                hamming_dist = query_hash - stored_hash  # 0 to 64
                # Normalize: 0 hamming = 1.0 score, 64 hamming = 0.0 score
                score = max(0.0, 1.0 - (hamming_dist / 64.0))
                if hamming_dist <= HAMMING_THRESHOLD:
                    candidates.append({"id": asset_id, "score": round(score, 6)})
            except Exception:
                continue

        return {
            "candidates": sorted(candidates, key=lambda c: c["score"], reverse=True)[:settings.TOP_K],
            "index_version": settings.INDEX_VERSION,
        }
