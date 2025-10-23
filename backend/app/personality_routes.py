"""
Personality management routes for My Mitra AI personalities.
Enhanced for Hacktober submission with comprehensive personality switching and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from .database import get_db
from .routes import get_current_user_optional
from .models import User
from llm.ollama_model import OllamaMyMitraModel, PersonalityType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personality", tags=["personality"])

# Global model instance for personality management
ollama_model = OllamaMyMitraModel()

@router.get("/available", response_model=List[Dict[str, str]])
async def get_available_personalities():
    """
    Get all available AI personalities with descriptions.
    Perfect for Hacktober demo - shows the distinct personality options.
    """
    try:
        personalities = ollama_model.get_available_personalities()
        logger.info(f"Retrieved {len(personalities)} available personalities")
        return personalities
    except Exception as e:
        logger.error(f"Error retrieving personalities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available personalities"
        )

@router.get("/current")
async def get_current_personality(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get the current active personality for the user.
    Returns personality info and user context.
    """
    try:
        personality_info = ollama_model.get_current_personality_info()
        
        # Add user context if available
        user_context = {}
        if current_user:
            user_context = {
                "user_id": current_user.id,
                "username": current_user.username,
                "has_custom_preferences": bool(current_user.role == "admin")
            }
        
        response = {
            **personality_info,
            "user_context": user_context,
            "status": "active"
        }
        
        logger.info(f"Current personality: {personality_info['type']} for user {current_user.id if current_user else 'anonymous'}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting current personality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current personality"
        )

@router.post("/switch/{personality_type}")
async def switch_personality(
    personality_type: str,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Switch to a different AI personality.
    Enhanced for Hacktober with validation and user tracking.
    """
    try:
        # Validate personality type
        try:
            personality_enum = PersonalityType(personality_type.lower())
        except ValueError:
            available_types = [p.value for p in PersonalityType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid personality type. Available: {available_types}"
            )
        
        # Switch personality
        ollama_model.set_personality(personality_enum)
        
        # Get updated personality info
        personality_info = ollama_model.get_current_personality_info()
        
        # Log the switch for analytics
        user_id = current_user.id if current_user else "anonymous"
        logger.info(f"User {user_id} switched to {personality_type} personality")
        
        return {
            "message": f"Successfully switched to {personality_info['name']}",
            "personality": personality_info,
            "switched_at": "now",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching personality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch personality"
        )

@router.get("/recommendations")
async def get_personality_recommendations(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get personality recommendations based on user context and time of day.
    Enhanced feature for Hacktober submission.
    """
    try:
        from datetime import datetime
        
        current_hour = datetime.now().hour
        
        # Time-based recommendations
        if 6 <= current_hour < 12:
            # Morning - energetic start
            recommended = "motivator"
            reason = "Morning energy boost to start your day strong!"
        elif 12 <= current_hour < 17:
            # Afternoon - focused work
            recommended = "coach"
            reason = "Afternoon focus time - perfect for strategic planning!"
        elif 17 <= current_hour < 21:
            # Evening - reflection
            recommended = "mentor"
            reason = "Evening reflection time for deeper insights!"
        else:
            # Night - gentle support
            recommended = "default"
            reason = "Late night support with gentle, caring guidance!"
        
        # Get personality details
        personalities = ollama_model.get_available_personalities()
        recommended_personality = next(
            (p for p in personalities if p["type"] == recommended), 
            personalities[0]
        )
        
        return {
            "recommended_personality": recommended_personality,
            "reason": reason,
            "time_context": {
                "current_hour": current_hour,
                "time_period": "morning" if 6 <= current_hour < 12 else 
                              "afternoon" if 12 <= current_hour < 17 else
                              "evening" if 17 <= current_hour < 21 else "night"
            },
            "all_personalities": personalities
        }
        
    except Exception as e:
        logger.error(f"Error getting personality recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personality recommendations"
        )

@router.post("/test/{personality_type}")
async def test_personality_response(
    personality_type: str,
    test_message: str = "Hello! I'm feeling a bit stressed about my upcoming exams.",
    current_user: User = Depends(get_current_user_optional)
):
    """
    Test a personality with a sample message without switching permanently.
    Perfect for Hacktober demo to showcase different personality styles.
    """
    try:
        # Validate personality type
        try:
            personality_enum = PersonalityType(personality_type.lower())
        except ValueError:
            available_types = [p.value for p in PersonalityType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid personality type. Available: {available_types}"
            )
        
        # Store current personality
        original_personality = ollama_model.current_personality
        
        try:
            # Temporarily switch to test personality
            ollama_model.set_personality(personality_enum)
            
            # Generate test response
            test_response = ollama_model.generate_response(
                test_message,
                conversation_history=[],
                long_term_memory_context=[],
                fast_mode=True
            )
            
            # Get personality info
            personality_info = ollama_model.get_current_personality_info()
            
            return {
                "personality": personality_info,
                "test_message": test_message,
                "test_response": test_response,
                "note": "This is a test response. Your actual personality hasn't changed."
            }
            
        finally:
            # Restore original personality
            ollama_model.set_personality(original_personality)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing personality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test personality"
        )

@router.get("/analytics")
async def get_personality_analytics(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get analytics about personality usage (for admin users).
    Enhanced feature for Hacktober admin dashboard.
    """
    try:
        # Basic analytics - in a real app, this would query usage logs
        analytics = {
            "current_session": {
                "active_personality": ollama_model.get_current_personality_info(),
                "session_duration": "active",
                "responses_generated": "tracking_enabled"
            },
            "personality_features": {
                "total_personalities": len(PersonalityType),
                "available_modes": [p.value for p in PersonalityType],
                "advanced_features": [
                    "Emotional context detection",
                    "Time-based recommendations", 
                    "Fallback response system",
                    "Human-like enhancement",
                    "Multi-user support"
                ]
            },
            "system_status": {
                "ollama_integration": "active",
                "personality_switching": "enabled",
                "response_enhancement": "active",
                "fallback_system": "ready"
            }
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting personality analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get personality analytics"
        )