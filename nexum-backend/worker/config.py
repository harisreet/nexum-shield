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

    # ─── FAISS Index Paths ────────────────────────────────────────
    FAISS_INDEX_GCS_PATH: str = "index/faiss.index"
    FAISS_ID_MAP_GCS_PATH: str = "index/id_map.json"
    FAISS_LOCAL_PATH: str = "/tmp/faiss.index"
    FAISS_ID_MAP_LOCAL_PATH: str = "/tmp/id_map.json"

    # ─── Model ────────────────────────────────────────────────────
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"
    MODEL_VERSION: str = "clip_v1"
    EMBEDDING_DIM: int = 512

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

    # ─── Server ───────────────────────────────────────────────────
    PORT: int = 8002
    LOG_LEVEL: str = "info"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
