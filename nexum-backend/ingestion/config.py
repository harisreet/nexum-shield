"""
NEXUM SHIELD — Ingestion API Config
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    GCP_PROJECT_ID: str = Field(default="nexum-local", env="GCP_PROJECT_ID")
    GCS_BUCKET: str = Field(default="nexum-assets", env="GCS_BUCKET")
    PUBSUB_TOPIC: str = Field(default="media-events", env="PUBSUB_TOPIC")

    USE_GCS_EMULATOR: bool = False
    GCS_EMULATOR_HOST: str = "http://localhost:4443"

    USE_PUBSUB_EMULATOR: bool = False
    PUBSUB_EMULATOR_HOST: str = "localhost:8085"

    PORT: int = 8001
    LOG_LEVEL: str = "info"

    ALLOWED_CONTENT_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    MAX_FILE_SIZE_MB: int = 20

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
