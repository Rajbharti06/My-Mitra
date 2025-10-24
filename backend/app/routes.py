from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Any, List
from pydantic import BaseModel
import os
import uuid
import logging

from . import crud, models, schemas, security
from .database import SessionLocal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import encryption_utils
from .enhanced_chat_pipeline import enhanced_chat_pipeline

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Security dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user_optional(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    if not token:
        return None
    try:
        user = security.get_current_user(token, db)
        return user
    except Exception:
        return None

async def get_current_user_required(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    user = security.get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

@router.post("/register", response_model=schemas.User)
def create_user(user: "schemas.UserCreate", db: "Session" = Depends(get_db)):
    db_user = crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/chat/", response_model=dict)
async def chat_with_mymitra(
    message: schemas.ChatMessageCreate, 
    current_user = Depends(get_current_user_optional),
    db: Any = Depends(get_db)
):
    """
    Chat with My Mitra AI with personality support.
    Supports both authenticated and anonymous users.
    """
    # Generate session ID if not provided
    session_id = message.session_id or str(uuid.uuid4())
    
    # Get AI response using enhanced pipeline
    result = enhanced_chat_pipeline.get_mitra_reply(
        user_input=message.message,
        user_id=current_user.id if current_user else None,
        db=db if current_user else None,
        personality=message.personality,
        session_id=session_id
    )
    
    # Analyze emotion if user is authenticated
    if current_user:
        try:
            from core.emotion_engine import analyze_emotion
            emotion_result = analyze_emotion(message.message)
            
            # Store emotion record
            emotion_record = models.EmotionRecord(
                user_id=current_user.id,
                primary_emotion=emotion_result.category.value,
                primary_intensity=emotion_result.intensity.value,
                confidence=emotion_result.confidence,
                sentiment_polarity=emotion_result.sentiment_scores.get("polarity", 0),
                sentiment_subjectivity=emotion_result.sentiment_scores.get("subjectivity", 0),
                text_snapshot=encryption_utils.encrypt_data(message.message).encode('utf-8')
            )
            db.add(emotion_record)
            db.commit()
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
    
    return result

@router.get("/chat/personalities", response_model=List[schemas.PersonalityInfo])
async def get_available_personalities():
    """Get list of available AI personalities."""
    return enhanced_chat_pipeline.get_available_personalities()

@router.get("/chat/history")
async def get_chat_history(
    limit: int = 20,
    session_id: Optional[str] = None,
    current_user = Depends(get_current_user_optional),
    db: Any = Depends(get_db)
):
    """Get user's chat history, optionally scoped to a session."""
    try:
        if not current_user:
            return {
                "messages": [],
                "total": 0
            }
        messages = crud.get_recent_chat_history(db, current_user.id, limit, session_id=session_id)
        return {
            "messages": messages,
            "total": len(messages)
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@router.get("/chat/sessions")
async def list_sessions(
    current_user = Depends(get_current_user_required),
    db: Any = Depends(get_db)
):
    """List distinct chat sessions for the authenticated user."""
    try:
        sessions = crud.list_chat_sessions(db, current_user.id)
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")

@router.delete("/chat/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user = Depends(get_current_user_required),
    db: Any = Depends(get_db)
):
    """Delete all messages within a specific chat session and verify deletion."""
    try:
        deleted_count = crud.delete_chat_session(db, current_user.id, session_id)
        # Verify deletion by re-querying
        remaining = crud.get_recent_chat_history(db, current_user.id, limit=1, session_id=session_id)
        return {
            "deleted": deleted_count,
            "verified": len(remaining) == 0
        }
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.delete("/chat/all")
async def delete_all_chats(
    current_user = Depends(get_current_user_required),
    db: Any = Depends(get_db)
):
    """Delete all chat messages for the authenticated user."""
    try:
        deleted_count = crud.delete_all_chats(db, current_user.id)
        # Verify deletion
        remaining_total = len(crud.get_recent_chat_history(db, current_user.id, limit=1))
        return {
            "deleted": deleted_count,
            "verified": remaining_total == 0
        }
    except Exception as e:
        logger.error(f"Error deleting all chats: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete all chats")

@router.post("/journal/")
async def create_journal_entry(journal: schemas.JournalCreate, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.create_journal(db, user_id=current_user.id, journal=journal)

@router.get("/journal/")
async def list_journal_entries(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_journals(db, user_id=current_user.id)

@router.post("/habits", response_model=schemas.Habit)
def create_habit(habit: "schemas.HabitCreate", db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    obj = crud.create_habit(db, user_id=current_user.id, habit=habit)
    # Log in long-term memory if available
    try:
        if enhanced_chat_pipeline.long_term_memory:
            enhanced_chat_pipeline.long_term_memory.add_memory(
                f"New habit created: {habit.title} - {habit.description}",
                {"session_id": current_user.username, "type": "habit_creation"}
            )
    except Exception:
        pass
    return obj

@router.get("/habits", response_model=list[schemas.Habit])
def list_habits(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_habits(db, user_id=current_user.id)

@router.post("/habits/{habit_id}/complete")
def complete_habit(habit_id: int, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    result = crud.complete_habit(db, user_id=current_user.id, habit_id=habit_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return result

@router.put("/habits/{habit_id}", response_model=schemas.Habit)
def update_habit(habit_id: int, habit_update: schemas.HabitUpdate, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    updated = crud.update_habit(db, user_id=current_user.id, habit_id=habit_id, habit_update=habit_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Habit not found")
    return updated

@router.post("/journals", response_model=schemas.Journal)
def create_journal(journal: "schemas.JournalCreate", db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    obj = crud.create_journal(db, user_id=current_user.id, journal=journal)
    try:
        if enhanced_chat_pipeline.long_term_memory:
            enhanced_chat_pipeline.long_term_memory.add_memory(
                f"New journal entry: {journal.content}",
                {"session_id": current_user.username, "type": "journal_entry", "mood": journal.mood}
            )
    except Exception:
        pass
    return schemas.Journal(id=obj.id, user_id=obj.user_id, content=journal.content)

@router.get("/journals", response_model=list[schemas.Journal])
def list_journals(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_journals(db, user_id=current_user.id)

@router.get("/habits/insights")
def habit_insights(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.get_habit_insights(db, user_id=current_user.id)

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "MyMitra backend is running"}

@router.get("/insights")
def get_insights(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    habits = crud.list_habits(db, user_id=current_user.id)
    journals = crud.list_journals(db, user_id=current_user.id)
    return {
        "summary": {
            "habit_count": len(habits),
            "journal_count": len(journals)
        },
        "habits": habits,
        "journals": journals
    }
