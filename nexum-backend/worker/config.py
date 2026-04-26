"""
NEXUM SHIELD — Centralized Configuration
Single source of truth for all thresholds, versions, and environment settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ─── GCP ──────────────────────────────────────────────────────
    GCP_PROJECT_ID: str = Field(default="nexum-local", env="GCP_PROJECT_ID")
    GCS_BUCKET: str = Field(default="nexum-assets", env="GCS_BUCKET")
    PUBSUB_TOPIC: str = Field(default="media-events", env="PUBSUB_TOPIC")
    PUBSUB_SUBSCRIPTION: str = Field(default="media-worker-sub", env="PUBSUB_SUBSCRIPTION")

    # ─── pHash Index Paths ────────────────────────────────────────
    FAISS_INDEX_GCS_PATH: str = "index/phash_index.json"
    FAISS_ID_MAP_GCS_PATH: str = "index/phash_index.json"  # same file
    FAISS_LOCAL_PATH: str = "/tmp/phash_index.json"
    FAISS_ID_MAP_LOCAL_PATH: str = "/tmp/phash_index.json"  # same file

    # ─── Model ────────────────────────────────────────────────────
    MODEL_VERSION: str = "phash_v1"
    HAMMING_THRESHOLD: int = 10   # bits different to consider a match (out of 64)

    # ─── Pipeline Thresholds (LOCKED — change requires policy bump) ─
    TOP_K: int = 5
    RISK_REVIEW_THRESHOLD: float = 0.70    # score >= this → REVIEW
    RISK_BLOCK_THRESHOLD: float = 0.90     # score >= this → BLOCK
    UNCERTAINTY_LOWER: float = 0.85        # uncertainty band lower
    UNCERTAINTY_UPPER: float = 0.90        # uncertainty band upper (= BLOCK)

    # ─── Versioning ───────────────────────────────────────────────
    INDEX_VERSION: str = "v1"
    POLICY_VERSION: str = "v1"

    # ─── Emulator Overrides (local dev) ───────────────────────────
    USE_GCS_EMULATOR: bool = False
    GCS_EMULATOR_HOST: str = "http://localhost:4443"

    USE_PUBSUB_EMULATOR: bool = False
    PUBSUB_EMULATOR_HOST: str = "localhost:8085"

    USE_FIRESTORE_EMULATOR: bool = False
    FIRESTORE_EMULATOR_HOST: str = "localhost:8086"

    # pHash requires no model — this flag is kept for API compatibility

    # ─── Server ───────────────────────────────────────────────────
    PORT: int = 8002
    LOG_LEVEL: str = "info"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
