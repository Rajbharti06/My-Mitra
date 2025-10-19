from sqlalchemy import Column, Integer, String, Text, Boolean
from .database import Base
from sqlalchemy import ForeignKey, LargeBinary, DateTime, func, UniqueConstraint

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    preferred_personality = Column(String, default="default")  # default, mentor, motivator, coach
    role = Column(String, default="user")  # user, admin, moderator
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    message_encrypted = Column(LargeBinary, nullable=False)  # User's message
    response_encrypted = Column(LargeBinary, nullable=False)  # AI's response
    personality_used = Column(String, nullable=False)  # Which personality was active
    session_id = Column(String, nullable=True)  # For grouping conversations
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title_encrypted = Column(LargeBinary, nullable=False)
    description_encrypted = Column(LargeBinary, nullable=True)
    frequency = Column(String, nullable=True)
    streak_count = Column(Integer, default=0)
    last_completed = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    content_encrypted = Column(LargeBinary, nullable=False)
    mood = Column(Integer)  # 1-10 scale
    tags = Column(String, nullable=True)  # Comma-separated tags
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, unique=True)
    chat_history_retention_days = Column(Integer, default=30)
    enable_long_term_memory = Column(Boolean, default=True)
    privacy_mode = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ResponseCache(Base):
    __tablename__ = "response_cache"

    id = Column(Integer, primary_key=True, index=True)
    question_key = Column(String, index=True, nullable=False)
    personality = Column(String, index=True, nullable=False)
    response_encrypted = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('question_key', 'personality', name='uq_response_cache_question_personality'),
    )
