"""
NEXUM SHIELD — Ingestion API Entry Point
Thin service: accepts uploads, stores to GCS, fires Pub/Sub events.
"""
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from services.gcs import ensure_bucket
from routes.upload import router as upload_router
from routes.health import router as health_router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("ingestion.startup")
    try:
        ensure_bucket()
    except Exception as e:
        log.warning("ingestion.bucket_check_failed", error=str(e))
    log.info("ingestion.ready")
    yield
    log.info("ingestion.shutdown")


app = FastAPI(
    title="NEXUM SHIELD — Ingestion API",
    description="Media upload and event dispatch service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("ingestion.unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level=settings.LOG_LEVEL)
