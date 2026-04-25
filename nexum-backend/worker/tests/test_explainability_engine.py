"""
NEXUM SHIELD — Unit Tests: Explainability Engine
Tests template coverage, determinism, and constraint compliance.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from engines.explainability.engine import ExplainabilityEngine

engine = ExplainabilityEngine()


def explain(risk_score=0.5, signals=None, candidates=None, decision="ALLOW"):
    return engine.process({
        "risk_score": risk_score,
        "signals": signals or [],
        "candidates": candidates or [],
        "decision": decision,
    })["explanation"]


# ── Template coverage ─────────────────────────────────────────────

def test_allow_explanation_contains_score():
    exp = explain(risk_score=0.40, decision="ALLOW")
    assert "40%" in exp


def test_review_explanation_contains_score():
    exp = explain(risk_score=0.75, signals=["high_similarity"], decision="REVIEW")
    assert "75%" in exp


def test_block_explanation_contains_score():
    exp = explain(risk_score=0.95, signals=["block_threshold"], decision="BLOCK")
    assert "BLOCKED" in exp
    assert "95%" in exp


def test_uncertainty_note_appears_in_band():
    exp = explain(risk_score=0.87, signals=["near_duplicate"], decision="REVIEW")
    assert "uncertainty band" in exp.lower()


def test_uncertainty_note_absent_outside_band():
    exp = explain(risk_score=0.80, decision="REVIEW")
    assert "uncertainty band" not in exp.lower()


# ── Constraint compliance ─────────────────────────────────────────

def test_explanation_is_string():
    result = engine.process({"risk_score": 0.5, "signals": [], "candidates": [], "decision": "ALLOW"})
    assert isinstance(result["explanation"], str)
    assert len(result["explanation"]) > 10


def test_no_match_summary_when_empty():
    exp = explain(risk_score=0.0, candidates=[], decision="ALLOW")
    assert "No reference matches" in exp


def test_top_match_appears_in_summary():
    candidates = [{"id": "abc123def456", "score": 0.91}]
    exp = explain(risk_score=0.91, signals=["block_threshold"], candidates=candidates, decision="BLOCK")
    assert "abc123de" in exp  # first 8 chars of ID


# ── Determinism invariant ─────────────────────────────────────────

def test_same_inputs_same_explanation():
    kwargs = dict(risk_score=0.88, signals=["near_duplicate"], decision="REVIEW",
                  candidates=[{"id": "xyz", "score": 0.88}])
    e1 = engine.process(kwargs)["explanation"]
    e2 = engine.process(kwargs)["explanation"]
    assert e1 == e2


# ── Signal formatting ─────────────────────────────────────────────

def test_signals_appear_in_explanation():
    exp = explain(risk_score=0.92, signals=["block_threshold", "near_duplicate"], decision="BLOCK")
    assert "block_threshold" in exp or "near_duplicate" in exp
