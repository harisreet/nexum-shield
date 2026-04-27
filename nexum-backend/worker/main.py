"""
NEXUM SHIELD — Worker Service Entry Point
Lifespan events load CLIP model + FAISS index at startup (once per container).
No business logic here — just wiring.
"""
import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from engines.embedding.engine import load_clip_model
from engines.matching.engine import load_faiss_index
from services import firestore as fs_service
from routes.process import router as process_router
from routes.admin import router as admin_router
from routes.health import router as health_router

# ─── Structured logging ───────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()


# ─── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load pHash index into memory."""
    log.info("worker.startup.begin")

    # Load pHash index from MongoDB/local disk into memory
    log.info("worker.startup.loading_index")
    load_faiss_index()

    # pHash requires no AI model download — startup is instant!
    load_clip_model()

    log.info("worker.startup.complete")
    yield

    log.info("worker.shutdown")


# ─── FastAPI App ──────────────────────────────────────────────────
app = FastAPI(
    title="NEXUM SHIELD — Worker",
    description="Pub/Sub-driven media analysis pipeline",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(process_router)
app.include_router(admin_router)


# ─── Global Exception Handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("worker.unhandled_exception", path=str(request.url), error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level=settings.LOG_LEVEL)
