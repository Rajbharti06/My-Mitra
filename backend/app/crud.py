from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas, security
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import encryption_utils
import json
import hashlib
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


def get_user_settings(db: Session, user_id: int) -> models.UserSettings:
    """Get or create per-user settings (adaptive memory opt-ins, retention)."""
    settings_obj = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
    if settings_obj:
        return settings_obj
    settings_obj = models.UserSettings(user_id=user_id)
    db.add(settings_obj)
    db.commit()
    db.refresh(settings_obj)
    return settings_obj


def update_user_memory_preferences(
    db: Session,
    user_id: int,
    prefs: schemas.MemoryPreferencesUpdate,
) -> models.UserSettings:
    """Update adaptive memory opt-in categories."""
    settings_obj = get_user_settings(db, user_id)
    settings_obj.allow_routine_tracking = bool(prefs.allow_routine_tracking)
    settings_obj.allow_preference_learning = bool(prefs.allow_preference_learning)
    settings_obj.allow_mental_health_inference = bool(prefs.allow_mental_health_inference)
    db.commit()
    db.refresh(settings_obj)
    return settings_obj


def update_memory_rate_limit_timestamps(
    db: Session,
    user_id: int,
    *,
    update_preference_at: Optional[datetime] = None,
    update_routine_at: Optional[datetime] = None,
) -> None:
    settings_obj = get_user_settings(db, user_id)
    if update_preference_at is not None:
        settings_obj.last_preference_memory_at = update_preference_at
    if update_routine_at is not None:
        settings_obj.last_routine_memory_at = update_routine_at
    db.commit()


# ---------------------------------------------------------------------------
# Identity Profile (Layer 7 — Identity Engine)
# ---------------------------------------------------------------------------

_IDENTITY_STABILITY_THRESHOLD = 2  # Pattern must repeat this many times to be promoted


def get_identity_profile(db: Session, user_id: int) -> Optional[models.UserIdentityProfile]:
    """Return the user's persistent identity profile, or None if it doesn't exist yet."""
    return (
        db.query(models.UserIdentityProfile)
        .filter(models.UserIdentityProfile.user_id == user_id)
        .first()
    )


def observe_identity_signal(
    db: Session,
    user_id: int,
    *,
    decision_pattern: Optional[str] = None,
    energy_cycle: Optional[str] = None,
    core_goal: Optional[str] = None,
    new_traits: Optional[List[str]] = None,
) -> models.UserIdentityProfile:
    """
    Record one observation of behavioural signals for a user.

    Each field has a tentative candidate and a stability counter:
    - If the new observation matches the current tentative value → increment counter.
    - If it differs → reset counter to 1 and update the tentative value.
    - When counter reaches _IDENTITY_STABILITY_THRESHOLD the value is promoted
      to "stable" and written to the main field.

    user_type is re-derived whenever decision_pattern or core_goal stabilises.
    core_traits_json is the union of all stable traits seen so far.
    """
    profile = get_identity_profile(db, user_id)
    if profile is None:
        profile = models.UserIdentityProfile(user_id=user_id)
        db.add(profile)
        db.flush()

    profile.observation_count = (profile.observation_count or 0) + 1

    # Confidence step sizes
    _CONF_STEP_MATCH = 0.3    # Confirmation strengthens belief
    _CONF_STEP_DECAY = 0.2    # Contradiction weakens existing stable field

    # --- decision_pattern ---
    if decision_pattern:
        if profile.tentative_decision_pattern == decision_pattern:
            # Confirmed match — raise confidence
            profile.decision_pattern_count = (profile.decision_pattern_count or 0) + 1
            profile.decision_pattern_confidence = min(
                1.0, (profile.decision_pattern_confidence or 0.0) + _CONF_STEP_MATCH
            )
        elif profile.tentative_decision_pattern is None:
            # First ever observation — seed tentative without penalising
            profile.tentative_decision_pattern = decision_pattern
            profile.decision_pattern_count = 1
        else:
            # Contradicting candidate — decay confidence in existing stable belief
            profile.decision_pattern_confidence = max(
                0.0, (profile.decision_pattern_confidence or 0.0) - _CONF_STEP_DECAY
            )
            profile.tentative_decision_pattern = decision_pattern
            profile.decision_pattern_count = 1
        if (profile.decision_pattern_count or 0) >= _IDENTITY_STABILITY_THRESHOLD:
            profile.decision_pattern = decision_pattern

    # --- energy_cycle ---
    if energy_cycle:
        if profile.tentative_energy_cycle == energy_cycle:
            profile.energy_cycle_count = (profile.energy_cycle_count or 0) + 1
            profile.energy_cycle_confidence = min(
                1.0, (profile.energy_cycle_confidence or 0.0) + _CONF_STEP_MATCH
            )
        elif profile.tentative_energy_cycle is None:
            profile.tentative_energy_cycle = energy_cycle
            profile.energy_cycle_count = 1
        else:
            profile.energy_cycle_confidence = max(
                0.0, (profile.energy_cycle_confidence or 0.0) - _CONF_STEP_DECAY
            )
            profile.tentative_energy_cycle = energy_cycle
            profile.energy_cycle_count = 1
        if (profile.energy_cycle_count or 0) >= _IDENTITY_STABILITY_THRESHOLD:
            profile.energy_cycle = energy_cycle

    # --- core_goal ---
    if core_goal:
        if profile.tentative_core_goal == core_goal:
            profile.core_goal_count = (profile.core_goal_count or 0) + 1
            profile.core_goal_confidence = min(
                1.0, (profile.core_goal_confidence or 0.0) + _CONF_STEP_MATCH
            )
        elif profile.tentative_core_goal is None:
            profile.tentative_core_goal = core_goal
            profile.core_goal_count = 1
        else:
            profile.core_goal_confidence = max(
                0.0, (profile.core_goal_confidence or 0.0) - _CONF_STEP_DECAY
            )
            profile.tentative_core_goal = core_goal
            profile.core_goal_count = 1
        if (profile.core_goal_count or 0) >= _IDENTITY_STABILITY_THRESHOLD:
            profile.core_goal = core_goal

    # --- core_traits (union accumulation — traits are additive once seen twice) ---
    if new_traits:
        existing: List[str] = []
        try:
            existing = json.loads(profile.core_traits_json or "[]")
        except Exception:
            existing = []
        merged = list(dict.fromkeys(existing + [t for t in new_traits if t]))
        profile.core_traits_json = json.dumps(merged[:10])  # cap at 10 traits

    # --- user_type (derived from stable decision_pattern + core_goal) ---
    dp = profile.decision_pattern
    cg = profile.core_goal
    if dp and cg:
        profile.user_type = f"{dp.replace('_', '-')} with {cg.replace('_', '-')} focus"
    elif dp:
        profile.user_type = dp.replace("_", " ")
    elif cg:
        profile.user_type = f"{cg.replace('_', '-')} focused"

    db.commit()
    db.refresh(profile)
    return profile


def identity_profile_to_dict(profile: Optional[models.UserIdentityProfile]) -> dict:
    """Serialize a UserIdentityProfile ORM object to a plain dict for pipeline use."""
    if profile is None:
        return {}
    traits: List[str] = []
    try:
        traits = json.loads(profile.core_traits_json or "[]")
    except Exception:
        pass
    return {
        "user_type": profile.user_type,
        "decision_pattern": profile.decision_pattern,
        "energy_cycle": profile.energy_cycle,
        "core_goal": profile.core_goal,
        "core_traits": traits,
        "observation_count": profile.observation_count or 0,
        # Confidence scores (0.0 – 1.0) for each stable field
        "confidence": {
            "decision_pattern": round(profile.decision_pattern_confidence or 0.0, 2),
            "energy_cycle": round(profile.energy_cycle_confidence or 0.0, 2),
            "core_goal": round(profile.core_goal_confidence or 0.0, 2),
        },
    }


def create_system_action_approval(
    db: Session,
    user_id: int,
    action_type: str,
    params: dict,
    summary: str,
    *,
    expires_minutes: int = 5,
) -> models.SystemActionApproval:
    """Create a pending approval record for an allowlisted system action."""
    # Canonicalize and hash the params to bind preview->execution.
    params_json = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    params_hash = hashlib.sha256(params_json.encode("utf-8")).hexdigest()
    params_encrypted = encryption_utils.encrypt_data(params_json).encode("utf-8")

    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    approval = models.SystemActionApproval(
        user_id=user_id,
        action_type=action_type,
        params_encrypted=params_encrypted,
        params_hash=params_hash,
        summary=summary,
        status="pending",
        expires_at=expires_at,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def get_system_action_approval_for_user(
    db: Session,
    user_id: int,
    approval_id: int,
) -> Optional[models.SystemActionApproval]:
    return (
        db.query(models.SystemActionApproval)
        .filter(models.SystemActionApproval.id == approval_id, models.SystemActionApproval.user_id == user_id)
        .first()
    )


def decide_system_action(
    db: Session,
    approval: models.SystemActionApproval,
    *,
    approve: bool,
    status_if_denied: str = "denied",
) -> models.SystemActionApproval:
    approval.status = status_if_denied if not approve else "approved"
    approval.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(approval)
    return approval


def mark_system_action_executed(
    db: Session,
    approval: models.SystemActionApproval,
    *,
    status: str,
    result_preview: Optional[str] = None,
    error_preview: Optional[str] = None,
) -> models.SystemActionApproval:
    approval.status = status  # executed/failed
    approval.executed_at = datetime.utcnow()
    approval.error_preview = error_preview

    if result_preview is not None:
        preview = result_preview[:5000]  # avoid huge DB rows
        approval.result_preview_encrypted = encryption_utils.encrypt_data(preview).encode("utf-8")

    db.commit()
    db.refresh(approval)
    return approval

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


def get_recent_chat_history(db: Session, user_id: int, limit: int = 10, session_id: Optional[str] = None) -> List[dict]:
    """Get recent chat history for context. If session_id provided, filter to that session."""
    query = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user_id)
    if session_id:
        query = query.filter(models.ChatMessage.session_id == session_id)
    messages = query.order_by(desc(models.ChatMessage.created_at)).limit(limit).all()
    
    result = []
    for msg in reversed(messages):  # Reverse to get chronological order
        try:
            user_message = encryption_utils.decrypt_data(msg.message_encrypted.decode('utf-8'))
            ai_response = encryption_utils.decrypt_data(msg.response_encrypted.decode('utf-8'))
            ts = msg.created_at.isoformat() if getattr(msg, 'created_at', None) else None
            sid = msg.session_id
            result.extend([
                {"role": "user", "content": user_message, "timestamp": ts, "session_id": sid},
                {"role": "assistant", "content": ai_response, "timestamp": ts, "session_id": sid}
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


def list_chat_sessions(db: Session, user_id: int) -> List[dict]:
    """List distinct chat sessions for a user with last activity timestamp."""
    # SQLite does not support DISTINCT ON; use subquery approach
    subq = db.query(models.ChatMessage.session_id, models.ChatMessage.created_at).\
        filter(models.ChatMessage.user_id == user_id).\
        order_by(models.ChatMessage.session_id, desc(models.ChatMessage.created_at)).subquery()
    rows = db.query(subq.c.session_id, subq.c.created_at).all()
    # Deduplicate keeping first occurrence (already sorted by created_at desc per session)
    seen = set()
    sessions = []
    for sid, ts in rows:
        if sid and sid not in seen:
            seen.add(sid)
            sessions.append({"id": sid, "last_activity": ts.isoformat() if ts else None})
    return sessions


def delete_chat_session(db: Session, user_id: int, session_id: str) -> int:
    """Delete all messages in a session for the user. Returns count deleted."""
    msgs = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == user_id,
        models.ChatMessage.session_id == session_id
    ).all()
    count = len(msgs)
    for m in msgs:
        db.delete(m)
    db.commit()
    return count


def delete_all_chats(db: Session, user_id: int) -> int:
    """Delete all chat messages for a user. Returns count deleted."""
    msgs = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user_id).all()
    count = len(msgs)
    for m in msgs:
        db.delete(m)
    db.commit()
    return count

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
    
    # Return formatted response like list_habits
    try:
        title = encryption_utils.decrypt_data(db_obj.title_encrypted.decode('utf-8'))
    except Exception:
        title = "[decryption_failed]"
    try:
        description = encryption_utils.decrypt_data(db_obj.description_encrypted.decode('utf-8')) if db_obj.description_encrypted else None
    except Exception:
        description = "[decryption_failed]"
    
    return {
        "id": db_obj.id,
        "user_id": db_obj.user_id,
        "title": title,
        "description": description,
        "frequency": db_obj.frequency,
        "streak_count": db_obj.streak_count,
        "last_completed": db_obj.last_completed.isoformat() if db_obj.last_completed else None,
        "created_at": db_obj.created_at.isoformat() if db_obj.created_at else None,
        "archived": db_obj.archived if hasattr(db_obj, 'archived') else False
    }


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

        # Validate current streak based on frequency
        if habit.last_completed:
            now = datetime.now()
            frequency = habit.frequency or 'daily'
            streak_broken = False
            
            if frequency == 'daily':
                days_since = (now - habit.last_completed).days
                if days_since > 1:  # More than 1 day gap breaks daily streak
                    streak_broken = True
            elif frequency == 'weekly':
                weeks_since = (now - habit.last_completed).days // 7
                if weeks_since > 1:  # More than 1 week gap breaks weekly streak
                    streak_broken = True
            elif frequency == 'monthly':
                months_since = (now.year - habit.last_completed.year) * 12 + (now.month - habit.last_completed.month)
                if months_since > 1:  # More than 1 month gap breaks monthly streak
                    streak_broken = True
            else:  # custom or unknown frequency, treat as daily
                days_since = (now - habit.last_completed).days
                if days_since > 1:
                    streak_broken = True
            
            if streak_broken:
                habit.streak_count = 0
                db.commit()  # Update the database with corrected streak
        
        result.append({
            "id": habit.id,
            "user_id": habit.user_id,
            "title": title,
            "description": description,
            "frequency": habit.frequency,
            "streak_count": habit.streak_count,
            "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
            "created_at": habit.created_at.isoformat() if habit.created_at else None,
            "archived": habit.archived if hasattr(habit, 'archived') else False
        })
    return result


def complete_habit(db: Session, user_id: int, habit_id: int):
    """Mark a habit as completed and update streak based on frequency."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()
    
    if not habit:
        return None
    
    now = datetime.now()
    frequency = habit.frequency or 'daily'
    
    # Check if already completed in the current period
    if habit.last_completed:
        if frequency == 'daily' and habit.last_completed.date() == now.date():
            return habit  # Already completed today
        elif frequency == 'weekly':
            # Check if completed in the same week
            last_week = habit.last_completed.isocalendar()[1]
            current_week = now.isocalendar()[1]
            if last_week == current_week and habit.last_completed.year == now.year:
                return habit  # Already completed this week
        elif frequency == 'monthly':
            # Check if completed in the same month
            if (habit.last_completed.month == now.month and 
                habit.last_completed.year == now.year):
                return habit  # Already completed this month
    
    # Calculate streak based on frequency
    if habit.last_completed:
        if frequency == 'daily':
            days_since = (now - habit.last_completed).days
            if days_since == 1:  # Consecutive day
                habit.streak_count += 1
            elif days_since > 1:  # Streak broken, restart
                habit.streak_count = 1
        elif frequency == 'weekly':
            weeks_since = (now - habit.last_completed).days // 7
            if weeks_since == 1:  # Consecutive week
                habit.streak_count += 1
            elif weeks_since > 1:  # Streak broken, restart
                habit.streak_count = 1
        elif frequency == 'monthly':
            # Calculate months between dates
            months_since = (now.year - habit.last_completed.year) * 12 + (now.month - habit.last_completed.month)
            if months_since == 1:  # Consecutive month
                habit.streak_count += 1
            elif months_since > 1:  # Streak broken, restart
                habit.streak_count = 1
        else:  # custom or unknown frequency, treat as daily
            days_since = (now - habit.last_completed).days
            if days_since <= 1:  # Within a day
                habit.streak_count += 1
            else:  # Streak broken, restart
                habit.streak_count = 1
    else:
        habit.streak_count = 1  # First completion
    
    habit.last_completed = now
    db.commit()
    
    return habit


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
    
    if habit_update.archived is not None:
        habit.archived = habit_update.archived
    
    habit.updated_at = datetime.now()
    db.commit()
    db.refresh(habit)
    
    # Return formatted response matching schemas.Habit (decrypt + ISO dates)
    try:
        title = encryption_utils.decrypt_data(habit.title_encrypted.decode('utf-8'))
    except Exception:
        title = "[decryption_failed]"
    try:
        description = encryption_utils.decrypt_data(habit.description_encrypted.decode('utf-8')) if habit.description_encrypted else None
    except Exception:
        description = "[decryption_failed]"

    return {
        "id": habit.id,
        "user_id": habit.user_id,
        "title": title,
        "description": description,
        "frequency": habit.frequency,
        "streak_count": habit.streak_count,
        "last_completed": habit.last_completed.isoformat() if habit.last_completed else None,
        "created_at": habit.created_at.isoformat() if habit.created_at else None,
        "archived": habit.archived if hasattr(habit, 'archived') else False
    }


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
