# app.py - FastAPI application configuration
"""
FastAPI application setup with CORS and middleware configuration
"""

import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from api.routes import router
from core.config import settings
from core.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce pymongo logging level to suppress debug messages
logging.getLogger('pymongo').setLevel(logging.WARNING)

_LOCAL = r"http://(127\.0\.0\.1|localhost)(:\d+)?"


def cors_origin_regex(extension_ids=()) -> str:
    """Pinned to the given extension IDs (plus localhost), or any extension origin if none are set."""
    if extension_ids:
        ids = "|".join(re.escape(i) for i in extension_ids)
        return rf"^((chrome|moz)-extension://({ids})|{_LOCAL})$"
    return rf"^((chrome|moz|safari-web|ms-browser)-extension://.+|{_LOCAL}|https://[\w-]+\.(vercel\.app|render\.com))$"


if not settings.EXTENSION_IDS and not settings.DEBUG:
    logger.warning("EXTENSION_IDS is not set: CORS accepts any browser extension origin. Set it to pin your extension.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Tube Snatcher Backend v3.0.0 starting; download directory: %s", settings.DEFAULT_DOWNLOAD_DIR)
    await db_manager.connect_to_database()
    yield
    logger.info("Shutting down")
    await db_manager.close_database()


# Initialize FastAPI app
app = FastAPI(
    title="Tube Snatcher Extension Backend",
    description="Backend API for YouTube video downloading browser extension",
    version="3.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Starlette matches allow_origins literally ("chrome-extension://*" never matched), so use a regex.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=cors_origin_regex(settings.EXTENSION_IDS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "service": "Tube Snatcher Extension Backend",
        "status": "running",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }