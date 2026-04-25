"""
NEXUM SHIELD — Unit Tests: Matching Engine
Tests the FAISS index integration with a live in-memory index.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pytest
from engines.matching.engine import (
    MatchingEngine,
    load_faiss_index,
    add_to_index,
    get_index_size,
    _index,
)
from engines.base import EngineError

# Bootstrap a fresh empty index for tests
import faiss
import engines.matching.engine as matching_module


@pytest.fixture(autouse=True)
def fresh_index():
    """Reset to a fresh empty index before each test."""
    matching_module._index = faiss.IndexFlatIP(512)
    matching_module._id_map = {}
    yield


engine = MatchingEngine()


def rand_unit_vector(dim=512, seed=None) -> list[float]:
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype(np.float32)
    v /= np.linalg.norm(v)
    return v.tolist()


# ── Empty index ───────────────────────────────────────────────────

def test_empty_index_returns_no_candidates():
    result = engine.process({"vector": rand_unit_vector(seed=1)})
    assert result["candidates"] == []
    assert "index_version" in result


# ── Add and search ────────────────────────────────────────────────

def test_add_and_find_vector():
    vec = rand_unit_vector(seed=42)
    add_to_index(vec, "asset-42")
    result = engine.process({"vector": vec})
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["id"] == "asset-42"
    assert result["candidates"][0]["score"] > 0.99  # self-match ≈ 1.0


def test_top_k_limits_results():
    for i in range(10):
        add_to_index(rand_unit_vector(seed=i), f"asset-{i}")
    result = engine.process({"vector": rand_unit_vector(seed=0)})
    assert len(result["candidates"]) <= 5  # TOP_K = 5


def test_results_ordered_by_score_descending():
    for i in range(5):
        add_to_index(rand_unit_vector(seed=i), f"asset-{i}")
    result = engine.process({"vector": rand_unit_vector(seed=0)})
    scores = [c["score"] for c in result["candidates"]]
    assert scores == sorted(scores, reverse=True)


def test_self_match_score_near_one():
    vec = rand_unit_vector(seed=99)
    add_to_index(vec, "self")
    result = engine.process({"vector": vec})
    top = result["candidates"][0]
    assert top["score"] > 0.999


# ── Error handling ────────────────────────────────────────────────

def test_missing_vector_raises_engine_error():
    with pytest.raises(EngineError):
        engine.process({})


# ── ID mapping ────────────────────────────────────────────────────

def test_id_map_returns_correct_asset():
    vec = rand_unit_vector(seed=7)
    add_to_index(vec, "unique-asset-id")
    result = engine.process({"vector": vec})
    assert result["candidates"][0]["id"] == "unique-asset-id"
