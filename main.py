"""
Fab's Beauty Salon — WhatsApp Chatbot
FastAPI application entry point.
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from webhook import router as webhook_router

# ── Logging configuration ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("fabs_chatbot")

# ── FastAPI application ────────────────────────────────────────────────
app = FastAPI(
    title="Fab's Beauty Salon Chatbot",
    description="WhatsApp chatbot for Fab's Beauty Salon via Meta WhatsApp Cloud API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# ── CORS (allow all for webhook compatibility) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──────────────────────────────────────────────────────
app.include_router(webhook_router)


# ── Health check ───────────────────────────────────────────────────────
@app.get("/health", tags=["monitoring"])
async def health_check() -> dict:
    """Liveness probe for monitoring and load balancers."""
    return {"status": "ok"}


# ── Startup / shutdown events ──────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Fab's Beauty Salon Chatbot is starting up…")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Fab's Beauty Salon Chatbot is shutting down…")


# ── Direct run (development only) ──────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
