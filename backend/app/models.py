from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy import ForeignKey, LargeBinary, DateTime, func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title_encrypted = Column(LargeBinary, nullable=False)
    description_encrypted = Column(LargeBinary, nullable=True)
    frequency = Column(String, nullable=True)
    streak_count = Column(Integer, default=0)
    last_completed = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    content_encrypted = Column(LargeBinary, nullable=False)
    mood = Column(Integer)  # 1-10 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())
