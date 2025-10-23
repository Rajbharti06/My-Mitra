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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_optional(db: Any = Depends(get_db)):
    try:
        # Return a default user for open access
        default_user = crud.get_user(db, "default_user")
        if not default_user:
            # Create a default user if it doesn't exist
            default_user = crud.create_user(db, schemas.UserCreate(
                username="default_user",
                email="default@example.com",
                password="default"
            ))
        return default_user
    except Exception as e:
        # If there's any database error, return None instead of failing
        print(f"Error in get_current_user_optional: {str(e)}")
        return None

async def get_current_user_required(db: Any = Depends(get_db)):
    try:
        # Return a default user for open access
        default_user = crud.get_user(db, "default_user")
        if not default_user:
            # Create a default user if it doesn't exist
            default_user = crud.create_user(db, schemas.UserCreate(
                username="default_user",
                email="default@example.com",
                password="default"
            ))
        return default_user
    except Exception as e:
        # If there's any database error, return None instead of failing
        print(f"Error in get_current_user_required: {str(e)}")
        return None

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: "Session" = Depends(get_db)):
    user = crud.get_user(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
                detection_method=emotion_result.detection_method,
                source_text=message.message,
                source_type="chat"
            )
            db.add(emotion_record)
            db.commit()
            
            # Add emotion data to response
            result["emotion_detected"] = {
                "primary_emotion": emotion_result.category.value,
                "intensity": emotion_result.intensity.value,
                "confidence": emotion_result.confidence
            }
        except Exception as e:
            # Log error but don't fail the chat request
            print(f"Error in emotion detection: {e}")
            pass
    
    return {
        "response": result["response"],
        "personality_used": result["personality_used"],
        "session_id": result["session_id"],
        "memory_used": result.get("memory_used", False),
        "personality_info": result.get("personality_info", {}),
        "user_authenticated": current_user is not None
    }

@router.post("/chat/personality", response_model=dict)
async def switch_personality(
    personality_data: schemas.PersonalitySwitch,
    current_user = Depends(get_current_user_optional),
    db: Any = Depends(get_db)
):
    """Switch AI personality mode."""
    result = enhanced_chat_pipeline.switch_personality(
        personality=personality_data.personality,
        user_id=current_user.id if current_user else None,
        db=db if current_user else None
    )
    return result

@router.get("/chat/personalities", response_model=List[schemas.PersonalityInfo])
async def get_available_personalities():
    """Get list of available AI personalities."""
    return enhanced_chat_pipeline.get_available_personalities()

@router.get("/chat/history")
async def get_chat_history(
    limit: int = 20,
    current_user = Depends(get_current_user_optional),
    db: Any = Depends(get_db)
):
    """Get user's chat history."""
    try:
        if not current_user:
            return {
                "messages": [],
                "total": 0
            }
        messages = crud.get_recent_chat_history(db, current_user.id, limit)
        return {
            "messages": messages,
            "total": len(messages)
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred")

@router.post("/journal/")
async def create_journal_entry(journal: schemas.JournalCreate, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.create_journal(db, user_id=current_user.id, journal=journal)

@router.get("/journal/")
async def list_journal_entries(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_journals(db, user_id=current_user.id)

@router.post("/habit/")
async def create_habit_entry(habit: schemas.HabitCreate, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.create_habit(db, user_id=current_user.id, habit=habit)

@router.get("/habit/")
async def list_habit_entries(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_habits(db, user_id=current_user.id)

@router.get("/insights/")
async def get_user_insights(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
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

@router.get("/me/export")
def export_data(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    habits = crud.list_habits(db, user_id=current_user.id)
    journals = crud.list_journals(db, user_id=current_user.id)

    export_data = {
        "user": current_user.username,
        "habits": [
            {
                "id": habit.id,
                "title": habit.title,
                "description": habit.description,
                "frequency": habit.frequency,
                "streak_count": habit.streak_count,
                "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
                "created_at": habit.created_at.isoformat(),
                "updated_at": habit.updated_at.isoformat()
            } for habit in habits
        ],
        "journals": [
            {
                "id": journal.id,
                "content": journal.content,
                "mood": journal.mood,
                "created_at": journal.created_at.isoformat()
            } for journal in journals
        ]
    }

    encrypted_data = encryption_utils.encrypt_data(str(export_data))

    return {"encrypted_data": encrypted_data}

@router.delete("/habits/{habit_id}")
def delete_habit(habit_id: int, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    success = crud.delete_habit(db, user_id=current_user.id, habit_id=habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"deleted": True}
