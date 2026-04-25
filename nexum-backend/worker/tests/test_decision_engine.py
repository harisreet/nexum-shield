"""
NEXUM SHIELD — Unit Tests: Decision Engine
Tests the locked policy table. No mocks needed — pure function.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from engines.decision.engine import DecisionEngine

engine = DecisionEngine()


def decide(score: float) -> str:
    return engine.process({"risk_score": score, "signals": []})["decision"]


# ── Policy table ──────────────────────────────────────────────────

def test_score_below_review_is_allow():
    assert decide(0.0)  == "ALLOW"
    assert decide(0.50) == "ALLOW"
    assert decide(0.69) == "ALLOW"


def test_score_at_review_threshold_is_review():
    assert decide(0.70) == "REVIEW"
    assert decide(0.75) == "REVIEW"
    assert decide(0.84) == "REVIEW"


def test_uncertainty_band_is_forced_review():
    """0.85–0.90 must ALWAYS be REVIEW (uncertainty guard)."""
    assert decide(0.85) == "REVIEW"
    assert decide(0.87) == "REVIEW"
    assert decide(0.8999) == "REVIEW"


def test_score_at_block_threshold_is_block():
    assert decide(0.90) == "BLOCK"
    assert decide(0.95) == "BLOCK"
    assert decide(1.00) == "BLOCK"


# ── Output shape ──────────────────────────────────────────────────

def test_output_contains_required_fields():
    result = engine.process({"risk_score": 0.5, "signals": []})
    assert "decision" in result
    assert "policy_version" in result
    assert "thresholds" in result


def test_thresholds_are_correct():
    result = engine.process({"risk_score": 0.5, "signals": []})
    t = result["thresholds"]
    assert t["review"] == 0.70
    assert t["block"]  == 0.90


# ── Determinism invariant ─────────────────────────────────────────

def test_same_score_same_decision():
    r1 = engine.process({"risk_score": 0.88, "signals": ["near_duplicate"]})
    r2 = engine.process({"risk_score": 0.88, "signals": ["near_duplicate"]})
    assert r1["decision"] == r2["decision"]


# ── Boundary conditions ───────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (0.6999, "ALLOW"),
    (0.7000, "REVIEW"),
    (0.8499, "REVIEW"),
    (0.8500, "REVIEW"),   # starts uncertainty band
    (0.8999, "REVIEW"),   # just before block
    (0.9000, "BLOCK"),    # exact block threshold
    (0.9001, "BLOCK"),
])
def test_boundary_values(score: float, expected: str):
    assert decide(score) == expected
