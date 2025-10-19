"""
My Mitra: Builder's Redemption - Enhanced Backend
An emotional AI companion for students with offline support and privacy-first design.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from . import models
from .database import engine
from .routes import router
from .config import settings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from llm.ollama_model import OllamaMyMitraModel

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mymitra.log") if not settings.DEBUG else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="My Mitra: Builder's Redemption",
    description="An emotional AI companion for students with offline support and privacy-first design",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting My Mitra backend...")
    
    # Validate configuration
    if not settings.validate_config() and not settings.DEBUG:
        logger.error("Invalid configuration detected!")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    # Test Ollama connection
    try:
        ollama_model = OllamaMyMitraModel()
        if ollama_model._check_ollama_connection():
            logger.info("✅ Ollama connection successful")
        else:
            logger.warning("⚠️ Ollama not available - using fallback responses")
    except Exception as e:
        logger.warning(f"⚠️ Ollama initialization failed: {e}")
    
    logger.info("🚀 My Mitra backend started successfully!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down My Mitra backend...")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "My Mitra Backend",
        "version": "2.0.0",
        "ollama_available": OllamaMyMitraModel()._check_ollama_connection()
    }

# Include API routes
app.include_router(router, prefix="/api/v1")

# Include personality management routes
from .personality_routes import router as personality_router
app.include_router(personality_router, prefix="/api/v1")

# Include admin routes
from .admin_routes import router as admin_router
app.include_router(admin_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "My Mitra: Builder's Redemption",
        "description": "An emotional AI companion for students",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Offline AI support via Ollama",
            "Multiple AI personalities",
            "Encrypted chat storage",
            "Habit tracking",
            "Journaling",
            "Privacy-first design"
        ]
    }
