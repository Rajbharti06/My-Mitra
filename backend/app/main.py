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
from .routers.emotions import router as emotions_router
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

# Ensure DB schema is up to date (add missing columns and performance indexes)
def ensure_db_schema():
    try:
        from .database import engine
        with engine.begin() as conn:
            cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()]
            if "preferred_personality" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN preferred_personality TEXT DEFAULT 'default'")
            if "role" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            if "is_active" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            if "created_at" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")

            # Create helpful indexes for chat performance (safe with IF NOT EXISTS)
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id)")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_chat_messages_user_session_created ON chat_messages(user_id, session_id, created_at)")
    except Exception as e:
        logger.warning(f"Schema check failed: {e}")

# Initialize FastAPI app
app = FastAPI(title="My Mitra: Builder's Redemption", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
models.Base.metadata.create_all(bind=engine)

# Ensure schema adjustments
ensure_db_schema()

# Include API routes
app.include_router(router, prefix="/api/v1")

# Include personality management routes
from .personality_routes import router as personality_router
app.include_router(personality_router, prefix="/api/v1")

# Include admin routes
from .admin_routes import router as admin_router
app.include_router(admin_router, prefix="/api/v1")

# Include emotion analysis routes
app.include_router(emotions_router, prefix="/api/v1")

# Include WebSocket routes
from .websocket_routes import router as websocket_router
app.include_router(websocket_router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to My Mitra API"}
