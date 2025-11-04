from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from .database import Base
from sqlalchemy import ForeignKey, LargeBinary, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship

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
    
    # Relationships
    emotion_records = relationship("EmotionRecord", back_populates="user")
    emotion_insights = relationship("EmotionInsight", back_populates="user")

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
    archived = Column(Boolean, default=False)
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

# Emotion models moved back here to avoid module/package conflicts
class EmotionRecord(Base):
    __tablename__ = "emotion_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=func.now())

    primary_emotion = Column(String, nullable=False)
    primary_intensity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    sentiment_polarity = Column(Float)
    sentiment_subjectivity = Column(Float)
    detection_method = Column(String)

    source_text = Column(String)
    source_type = Column(String, default="chat")

    user = relationship("User", back_populates="emotion_records")

class EmotionInsight(Base):
    __tablename__ = "emotion_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, server_default=func.now())

    time_period = Column(String)
    insight_text = Column(String, nullable=False)

    dominant_emotion = Column(String)
    emotion_distribution = Column(String)  # JSON string

    user = relationship("User", back_populates="emotion_insights")

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
