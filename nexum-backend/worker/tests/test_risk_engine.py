"""
NEXUM SHIELD — Unit Tests: Risk Engine
Tests deterministic scoring. No mocks needed — pure function.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from engines.risk.engine import RiskEngine

engine = RiskEngine()


# ── Core determinism ──────────────────────────────────────────────

def test_risk_is_max_of_candidates():
    result = engine.process({"candidates": [
        {"id": "a", "score": 0.75},
        {"id": "b", "score": 0.92},
        {"id": "c", "score": 0.88},
    ]})
    assert result["risk_score"] == pytest.approx(0.92, abs=1e-5)


def test_empty_candidates_returns_zero():
    result = engine.process({"candidates": []})
    assert result["risk_score"] == 0.0
    assert "no_matches" in result["signals"]


def test_no_candidates_key_returns_zero():
    result = engine.process({})
    assert result["risk_score"] == 0.0


def test_single_candidate():
    result = engine.process({"candidates": [{"id": "x", "score": 0.55}]})
    assert result["risk_score"] == pytest.approx(0.55, abs=1e-5)


# ── Signal generation ─────────────────────────────────────────────

def test_block_threshold_signals():
    result = engine.process({"candidates": [{"id": "x", "score": 0.95}]})
    assert "block_threshold" in result["signals"]
    assert "near_duplicate" in result["signals"]
    assert "high_similarity" in result["signals"]


def test_review_threshold_signals():
    result = engine.process({"candidates": [{"id": "x", "score": 0.75}]})
    assert "high_similarity" in result["signals"]
    assert "block_threshold" not in result["signals"]
    assert "near_duplicate" not in result["signals"]


def test_allow_no_signals():
    result = engine.process({"candidates": [{"id": "x", "score": 0.50}]})
    assert result["signals"] == []


# ── Determinism invariant ─────────────────────────────────────────

def test_same_input_same_output():
    inp = {"candidates": [{"id": "a", "score": 0.87}]}
    r1 = engine.process(inp)
    r2 = engine.process(inp)
    assert r1["risk_score"] == r2["risk_score"]
    assert r1["signals"] == r2["signals"]


def test_score_precision():
    result = engine.process({"candidates": [{"id": "x", "score": 0.912345678}]})
    # Must be rounded to 6 decimal places
    assert len(str(result["risk_score"]).split(".")[-1]) <= 7
