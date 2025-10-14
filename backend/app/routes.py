from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Any
from pydantic import BaseModel
import os

from . import crud, models, schemas, security
from .database import SessionLocal
from .. import encryption_utils
from ..llm.model import MyMitraModel
from ..llm.cbt_logic import CBTLogic
from ..vector_memory import LongTermMemory
from .chat_pipeline import get_mitra_reply

router = APIRouter()

# Determine echo-only mode for AI components only
ECHO_ONLY = os.environ.get("MYMITRA_ECHO_ONLY") == "1"

if not ECHO_ONLY:
    my_mitra_model = MyMitraModel()
    cbt_agent = CBTLogic(my_mitra_model)
    long_term_memory = LongTermMemory()
else:
    my_mitra_model = None
    cbt_agent = None
    long_term_memory = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: Any = Depends(get_db)):
    if not token:
        return None
    try:
        token_data = security.verify_token(token, HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ))
        user = crud.get_user(db, username=token_data.username)
        return user
    except Exception:
        return None

async def get_current_user_required(token: str | None = Depends(oauth2_scheme), db: Any = Depends(get_db)):
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.verify_token(token, credentials_exception)
    user = crud.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

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

class Message(BaseModel):
    user_input: str

@router.post("/chat/")
async def chat_with_mymitra(message: Message, current_user = Depends(get_current_user_optional)):
    user_id = current_user.username if current_user else "anonymous"
    reply = get_mitra_reply(user_id=user_id, user_message=message.user_input)
    return {"response": reply}

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
    if long_term_memory:
        long_term_memory.add_memory(f"New habit created: {habit.title} - {habit.description}", {"session_id": current_user.username, "type": "habit_creation"})
    return obj

@router.get("/habits", response_model=list[schemas.Habit])
def list_habits(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_habits(db, user_id=current_user.id)

@router.post("/habits/{habit_id}/complete")
def complete_habit(habit_id: int, db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.user_id == current_user.id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    from datetime import datetime
    today = datetime.now()
    
    if habit.last_completed and habit.last_completed.date() == today.date():
        return {"message": "Already completed today"}
    
    if habit.last_completed and (today - habit.last_completed).days == 1:
        habit.streak_count += 1
    elif not habit.last_completed or (today - habit.last_completed).days > 1:
        habit.streak_count = 1
    
    habit.last_completed = today
    db.commit()
    return {"message": "Habit completed!", "streak": habit.streak_count}

@router.post("/journals", response_model=schemas.Journal)
def create_journal(journal: "schemas.JournalCreate", db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    obj = crud.create_journal(db, user_id=current_user.id, journal=journal)
    if long_term_memory:
        long_term_memory.add_memory(f"New journal entry: {journal.content}", {"session_id": current_user.username, "type": "journal_entry", "mood": journal.mood})
    return schemas.Journal(id=obj.id, user_id=obj.user_id, content=journal.content)

@router.get("/journals", response_model=list[schemas.Journal])
def list_journals(db: "Session" = Depends(get_db), current_user=Depends(get_current_user_required)):
    return crud.list_journals(db, user_id=current_user.id)

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
