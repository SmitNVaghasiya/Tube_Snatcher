# app.py - FastAPI application configuration
"""
FastAPI application setup with CORS and middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
import logging

from api.routes import router
from core.download_manager import DownloadManager
from core.config import settings
from core.database import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Tube Snatcher Extension Backend",
    description="Backend API for YouTube video downloading browser extension",
    version="3.0.0",  # Updated version
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware for browser extension compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Chrome extensions
        "moz-extension://*",     # Firefox extensions
        "safari-web-extension://*",  # Safari extensions
        "ms-browser-extension://*",  # Edge extensions
        "http://127.0.0.1:*",    # Local development
        "http://localhost:*",    # Local development
        "https://*.vercel.app",  # Vercel deployments
        "https://*.render.com",  # Render deployments
        "https://yourdomain.com",  # Your domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize managers
download_manager = DownloadManager()

# Add managers to app state
app.state.download_manager = download_manager

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"🎬 Tube Snatcher Backend v3.0.0 starting at {datetime.now()}")
    print(f"📂 Default download directory: {settings.DEFAULT_DOWNLOAD_DIR}")
    
    # Connect to database
    await db_manager.connect_to_database()
    
    # Start the download manager
    await download_manager.start()
    
    print("✅ All systems initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Tube Snatcher Backend...")
    
    # Stop download manager
    await download_manager.stop()
    
    # Close database connection
    await db_manager.close_database()
    
    print("✅ All systems shut down")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "service": "Tube Snatcher Extension Backend",
        "status": "running",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "CORS preflight handled"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }