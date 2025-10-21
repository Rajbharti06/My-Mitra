"""
Database models for emotion tracking and analysis
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base

class EmotionRecord(Base):
    """Model for storing user emotion records over time"""
    __tablename__ = "emotion_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Primary emotion data
    primary_emotion = Column(String, nullable=False)
    primary_intensity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Additional data
    sentiment_polarity = Column(Float)
    sentiment_subjectivity = Column(Float)
    detection_method = Column(String)
    
    # Source of the emotion detection
    source_text = Column(String)
    source_type = Column(String, default="chat")  # chat, journal, etc.
    
    # Relationships
    user = relationship("User", back_populates="emotion_records")
    
    def __repr__(self):
        return f"<EmotionRecord(user_id={self.user_id}, emotion={self.primary_emotion}, intensity={self.primary_intensity})>"


class EmotionInsight(Base):
    """Model for storing generated insights about user emotions"""
    __tablename__ = "emotion_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Insight data
    time_period = Column(String)  # day, week, month
    insight_text = Column(String, nullable=False)
    
    # Emotion statistics
    dominant_emotion = Column(String)
    emotion_distribution = Column(String)  # JSON string of emotion distribution
    
    # Relationships
    user = relationship("User", back_populates="emotion_insights")
    
    def __repr__(self):
        return f"<EmotionInsight(user_id={self.user_id}, time_period={self.time_period})>"