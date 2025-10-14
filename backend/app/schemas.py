from pydantic import BaseModel, ConfigDict
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Habit Schemas ---
class HabitBase(BaseModel):
    title: str
    description: Optional[str] = None
    frequency: Optional[str] = None

class HabitCreate(HabitBase):
    pass

class Habit(HabitBase):
    id: int
    user_id: int
    streak_count: Optional[int] = 0
    last_completed: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

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
