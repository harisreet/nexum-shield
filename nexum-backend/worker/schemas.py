"""
NEXUM SHIELD — Data Schemas (Worker)
All input/output contracts for the pipeline. These are LOCKED — changes require version bump.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


# ─── Pipeline Intermediates ───────────────────────────────────────

class PreprocessOutput(BaseModel):
    phash: str
    width: int
    height: int
    local_path: str  # path to preprocessed image on disk


class EmbeddingOutput(BaseModel):
    vector: list[float]
    model: str
    embedding_version: str


class Candidate(BaseModel):
    id: str
    score: float


class MatchingOutput(BaseModel):
    candidates: list[Candidate]
    index_version: str


class RiskOutput(BaseModel):
    risk_score: float
    signals: list[str]


class DecisionOutput(BaseModel):
    decision: Literal["ALLOW", "REVIEW", "BLOCK"]
    policy_version: str
    thresholds: dict


class ExplainabilityOutput(BaseModel):
    explanation: str


# ─── Pub/Sub Message ──────────────────────────────────────────────

class PubSubEvent(BaseModel):
    trace_id: str
    asset_id: str
    gcs_path: str
    source: str = "api"
    timestamp: str


class PubSubMessage(BaseModel):
    """Pub/Sub push message envelope."""
    data: str   # base64-encoded PubSubEvent JSON
    messageId: Optional[str] = None
    publishTime: Optional[str] = None


class PubSubPushRequest(BaseModel):
    message: PubSubMessage
    subscription: Optional[str] = None


# ─── Final Decision Record ────────────────────────────────────────

class DecisionRecord(BaseModel):
    """Immutable record written to Firestore decisions collection."""
    trace_id: str
    asset_id: str
    risk_score: float
    decision: Literal["ALLOW", "REVIEW", "BLOCK"]
    signals: list[str]
    explanation: str
    matches: list[Candidate]
    model_version: str
    index_version: str
    policy_version: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ─── API Response ─────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    trace_id: str
    asset_id: str
    risk_score: float
    decision: Literal["ALLOW", "REVIEW", "BLOCK"]
    signals: list[str]
    explanation: str
    matches: list[Candidate]
    model_version: str
    index_version: str
    policy_version: str


# ─── Admin ────────────────────────────────────────────────────────

class IndexStats(BaseModel):
    total_vectors: int
    index_version: str
    model_version: str
    index_on_disk: bool


class SeedResponse(BaseModel):
    asset_id: str
    message: str
