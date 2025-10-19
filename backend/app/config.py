"""
Configuration management for My Mitra backend.
Handles environment variables and application settings.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mymitra.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "your-32-character-encryption-key")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral:latest")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "30"))
    
    # Chat Settings
    DEFAULT_PERSONALITY: str = os.getenv("DEFAULT_PERSONALITY", "default")
    ENABLE_LONG_TERM_MEMORY: bool = os.getenv("ENABLE_LONG_TERM_MEMORY", "true").lower() == "true"
    MAX_CHAT_HISTORY: int = int(os.getenv("MAX_CHAT_HISTORY", "50"))
    CHAT_RETENTION_DAYS: int = int(os.getenv("CHAT_RETENTION_DAYS", "30"))
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:3001"
    ).split(",")
    
    # Personality configurations
    PERSONALITIES = {
        "mentor": {
            "name": "Mentor",
            "description": "Wise, patient guide focused on long-term growth and learning",
            "emoji": "🧙‍♂️"
        },
        "motivator": {
            "name": "Motivator", 
            "description": "Energetic, encouraging companion that boosts confidence",
            "emoji": "🚀"
        },
        "coach": {
            "name": "Coach",
            "description": "Goal-oriented, structured approach to achieving objectives",
            "emoji": "🏆"
        },
        "default": {
            "name": "Default",
            "description": "Balanced, empathetic AI companion for general support",
            "emoji": "🤖"
        }
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration settings."""
        if cls.SECRET_KEY == "your-secret-key-change-this-in-production":
            print("WARNING: Using default SECRET_KEY. Change this in production!")
            return False
            
        if cls.ENCRYPTION_KEY == "your-32-character-encryption-key":
            print("WARNING: Using default ENCRYPTION_KEY. Change this in production!")
            return False
            
        if len(cls.ENCRYPTION_KEY) != 32:
            print("ERROR: ENCRYPTION_KEY must be exactly 32 characters long!")
            return False
            
        return True

# Global settings instance
settings = Settings()

# Legacy config for backward compatibility
CONFIG = {
    "local_llm_url": settings.OLLAMA_BASE_URL,
    "ollama_model": settings.OLLAMA_MODEL,
    "debug": settings.DEBUG
}

