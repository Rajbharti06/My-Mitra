from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = "user"

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    preferred_personality: Optional[str] = "default"
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- Chat Schemas ---
class ChatMessageCreate(BaseModel):
    message: str
    personality: Optional[str] = None
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    message: str
    response: str
    personality_used: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PersonalityInfo(BaseModel):
    type: str
    name: str
    description: str

class PersonalitySwitch(BaseModel):
    personality: str

# --- Habit Schemas ---
class HabitBase(BaseModel):
    title: str
    description: Optional[str] = None
    frequency: Optional[str] = None

class HabitCreate(HabitBase):
    pass

class Habit(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    frequency: Optional[str] = None
    streak_count: Optional[int] = 0
    last_completed: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    is_active: Optional[bool] = None

# --- Journal Schemas ---
class JournalBase(BaseModel):
    content: str
    mood: Optional[int] = None

class JournalCreate(JournalBase):
    pass

class Journal(JournalBase):
    id: int
    user_id: int
    created_at: str # Add created_at field

    model_config = ConfigDict(from_attributes=True)
