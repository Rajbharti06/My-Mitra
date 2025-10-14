from sqlalchemy.orm import Session
from . import models, schemas, security
from .. import encryption_utils
from datetime import datetime

# Users

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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
