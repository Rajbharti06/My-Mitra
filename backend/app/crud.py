from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas, security
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import encryption_utils
from datetime import datetime, timedelta
from typing import List, Optional

# Users

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """Get user by email address."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default user settings
    user_settings = models.UserSettings(user_id=db_user.id)
    db.add(user_settings)
    db.commit()
    
    return db_user

def update_user_personality(db: Session, user_id: int, personality: str):
    """Update user's preferred personality."""
    db.query(models.User).filter(models.User.id == user_id).update(
        {"preferred_personality": personality}
    )
    db.commit()
    return True

# Chat Messages

def create_chat_message(
    db: Session, 
    user_id: int, 
    message: str, 
    response: str, 
    personality_used: str,
    session_id: Optional[str] = None
):
    """Store an encrypted chat message and response."""
    db_message = models.ChatMessage(
        user_id=user_id,
        message_encrypted=encryption_utils.encrypt_data(message).encode('utf-8'),
        response_encrypted=encryption_utils.encrypt_data(response).encode('utf-8'),
        personality_used=personality_used,
        session_id=session_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_recent_chat_history(db: Session, user_id: int, limit: int = 10) -> List[dict]:
    """Get recent chat history for context."""
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == user_id
    ).order_by(desc(models.ChatMessage.created_at)).limit(limit).all()
    
    result = []
    for msg in reversed(messages):  # Reverse to get chronological order
        try:
            user_message = encryption_utils.decrypt_data(msg.message_encrypted.decode('utf-8'))
            ai_response = encryption_utils.decrypt_data(msg.response_encrypted.decode('utf-8'))
            result.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ])
        except Exception:
            continue  # Skip corrupted messages
    
    return result

def get_chat_messages_for_export(db: Session, user_id: int) -> List[dict]:
    """Get all chat messages for data export."""
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == user_id
    ).order_by(models.ChatMessage.created_at).all()
    
    result = []
    for msg in messages:
        try:
            user_message = encryption_utils.decrypt_data(msg.message_encrypted.decode('utf-8'))
            ai_response = encryption_utils.decrypt_data(msg.response_encrypted.decode('utf-8'))
            result.append({
                "timestamp": msg.created_at.isoformat(),
                "user_message": user_message,
                "ai_response": ai_response,
                "personality": msg.personality_used,
                "session_id": msg.session_id
            })
        except Exception:
            continue
    
    return result

# Habits

def create_habit(db: Session, user_id: int, habit: schemas.HabitCreate):
    db_obj = models.Habit(
        user_id=user_id,
        title_encrypted=encryption_utils.encrypt_data(habit.title).encode('utf-8'),
        description_encrypted=encryption_utils.encrypt_data(habit.description).encode('utf-8') if habit.description else None,
        frequency=habit.frequency,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def list_habits(db: Session, user_id: int):
    habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).all()
    result = []
    for habit in habits:
        try:
            title = encryption_utils.decrypt_data(habit.title_encrypted.decode('utf-8'))
        except Exception:
            title = "[decryption_failed]"
        try:
            description = encryption_utils.decrypt_data(habit.description_encrypted.decode('utf-8')) if habit.description_encrypted else None
        except Exception:
            description = "[decryption_failed]"

        # Calculate current streak for each habit
        if habit.last_completed:
            days_since = (datetime.now() - habit.last_completed).days
            if days_since > 1:  # Streak broken
                habit.streak_count = 0
        
        result.append({
            "id": habit.id,
            "user_id": habit.user_id,
            "title": title,
            "description": description,
            "frequency": habit.frequency,
            "streak_count": habit.streak_count,
            "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
            "created_at": habit.created_at.isoformat() if habit.created_at else None
        })
    return result


def complete_habit(db: Session, user_id: int, habit_id: int):
    """Mark a habit as completed for today and update streak."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()
    
    if not habit:
        return None
    
    now = datetime.now()
    
    # Check if already completed today
    if habit.last_completed and habit.last_completed.date() == now.date():
        return {"message": "Habit already completed today", "streak": habit.streak_count}
    
    # Update streak logic
    if habit.last_completed:
        days_since = (now - habit.last_completed).days
        if days_since == 1:  # Consecutive day
            habit.streak_count += 1
        elif days_since > 1:  # Streak broken, restart
            habit.streak_count = 1
    else:
        habit.streak_count = 1  # First completion
    
    habit.last_completed = now
    db.commit()
    
    return {
        "message": "Habit completed successfully!",
        "streak": habit.streak_count,
        "last_completed": habit.last_completed.isoformat()
    }


def get_habit_insights(db: Session, user_id: int):
    """Get emotional insights and analytics for user's habits."""
    habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).all()
    
    total_habits = len(habits)
    active_habits = len([h for h in habits if h.is_active])
    
    # Calculate completion rates and streaks
    completion_data = []
    total_streak = 0
    
    for habit in habits:
        try:
            title = encryption_utils.decrypt_data(habit.title_encrypted.decode('utf-8'))
        except Exception:
            title = "[decryption_failed]"
        
        # Calculate completion rate (last 7 days)
        days_since_created = (datetime.now() - habit.created_at).days
        expected_completions = min(7, days_since_created + 1)
        
        # Simple completion rate based on streak vs expected
        completion_rate = min(100, (habit.streak_count / max(1, expected_completions)) * 100)
        
        completion_data.append({
            "habit_title": title,
            "streak": habit.streak_count,
            "completion_rate": round(completion_rate, 1),
            "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
            "frequency": habit.frequency
        })
        
        total_streak += habit.streak_count
    
    # Generate emotional insights
    insights = []
    
    if total_streak > 20:
        insights.append({
            "type": "celebration",
            "message": "🎉 Amazing! Your combined streak is over 20 days. You're building incredible momentum!",
            "emotional_tone": "proud"
        })
    elif total_streak > 10:
        insights.append({
            "type": "encouragement",
            "message": "💪 Great progress! You're developing strong habits. Keep the momentum going!",
            "emotional_tone": "motivated"
        })
    elif total_streak > 0:
        insights.append({
            "type": "support",
            "message": "🌱 Every small step counts. You're on the right path to building lasting habits.",
            "emotional_tone": "supportive"
        })
    else:
        insights.append({
            "type": "gentle_nudge",
            "message": "🤗 Starting is the hardest part. Choose one small habit to focus on today.",
            "emotional_tone": "caring"
        })
    
    # Add specific insights based on patterns
    if active_habits > 5:
        insights.append({
            "type": "advice",
            "message": "💡 You have many habits tracked. Consider focusing on 2-3 core habits for better success.",
            "emotional_tone": "wise"
        })
    
    return {
        "total_habits": total_habits,
        "active_habits": active_habits,
        "total_streak": total_streak,
        "completion_data": completion_data,
        "insights": insights,
        "generated_at": datetime.now().isoformat()
    }


def update_habit(db: Session, user_id: int, habit_id: int, habit_update: schemas.HabitUpdate):
    """Update an existing habit."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()
    
    if not habit:
        return None
    
    # Update fields if provided
    if habit_update.title:
        habit.title_encrypted = encryption_utils.encrypt_data(habit_update.title).encode('utf-8')
    
    if habit_update.description is not None:
        habit.description_encrypted = encryption_utils.encrypt_data(habit_update.description).encode('utf-8') if habit_update.description else None
    
    if habit_update.frequency:
        habit.frequency = habit_update.frequency
    
    if habit_update.is_active is not None:
        habit.is_active = habit_update.is_active
    
    habit.updated_at = datetime.now()
    db.commit()
    db.refresh(habit)
    
    return habit


def delete_habit(db: Session, user_id: int, habit_id: int):
    """Delete a habit."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()
    
    if not habit:
        return False
    
    db.delete(habit)
    db.commit()
    return True

# Response Cache

def get_cached_response(
    db: Session,
    question_key: str,
    personality: str,
    ttl_minutes: int = 10080  # default 7 days
) -> Optional[str]:
    """Return decrypted cached response if fresh, otherwise None.
    Cache is keyed by normalized question text and personality.
    """
    try:
        entry = db.query(models.ResponseCache).filter(
            models.ResponseCache.question_key == question_key,
            models.ResponseCache.personality == personality
        ).first()
        if not entry:
            return None
        # Check TTL freshness
        cutoff = datetime.utcnow() - timedelta(minutes=ttl_minutes)
        created = entry.created_at if entry.created_at else datetime.utcnow()
        # created may be timezone-aware; fallback safe comparison
        is_fresh = True
        try:
            is_fresh = created >= cutoff
        except Exception:
            is_fresh = True
        if not is_fresh:
            return None
        try:
            return encryption_utils.decrypt_data(entry.response_encrypted.decode('utf-8'))
        except Exception:
            return None
    except Exception:
        return None


def upsert_cached_response(
    db: Session,
    question_key: str,
    personality: str,
    response: str
) -> bool:
    """Insert or update encrypted cached response.
    Returns True on success.
    """
    try:
        encrypted = encryption_utils.encrypt_data(response).encode('utf-8')
        entry = db.query(models.ResponseCache).filter(
            models.ResponseCache.question_key == question_key,
            models.ResponseCache.personality == personality
        ).first()
        if entry:
            entry.response_encrypted = encrypted
        else:
            entry = models.ResponseCache(
                question_key=question_key,
                personality=personality,
                response_encrypted=encrypted
            )
            db.add(entry)
        db.commit()
        return True
    except Exception:
        return False

# Journals (encrypted at rest)

def create_journal(db: Session, user_id: int, journal: schemas.JournalCreate):
    encrypted = encryption_utils.encrypt_data(journal.content).encode('utf-8')
    db_obj = models.Journal(
        user_id=user_id,
        content_encrypted=encrypted,
        mood=journal.mood,
        created_at=datetime.now() # Set created_at to current time
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def list_journals(db: Session, user_id: int):
    items = db.query(models.Journal).filter(models.Journal.user_id == user_id).all()
    # map to API schema shape with decrypted content
    result = []
    for it in items:
        try:
            content = encryption_utils.decrypt_data(it.content_encrypted.decode('utf-8'))
        except Exception:
            content = "[decryption_failed]"
        result.append({
            "id": it.id,
            "user_id": it.user_id,
            "content": content,
            "mood": it.mood,
            "created_at": it.created_at.isoformat() if it.created_at else None
        })
    return result
