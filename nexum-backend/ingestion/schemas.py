"""
NEXUM SHIELD — Ingestion API Schemas
"""
from pydantic import BaseModel
from typing import Optional, Literal


class UploadResponse(BaseModel):
    asset_id: str
    trace_id: str
    status: Literal["processing"] = "processing"
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
