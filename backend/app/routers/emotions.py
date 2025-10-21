"""
FastAPI router for emotion analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..models.emotion import EmotionRecord, EmotionInsight
from ..schemas import EmotionResponse, EmotionAnalysisRequest, EmotionInsightResponse
from ...core.emotion_engine import emotion_engine, EmotionCategory, EmotionIntensity

router = APIRouter(
    prefix="/emotions",
    tags=["emotions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyze", response_model=EmotionResponse)
async def analyze_emotion(
    request: EmotionAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze text for emotional content and return detected emotions
    """
    # Analyze text with emotion engine
    emotion_data = emotion_engine.detect_emotion(request.text)
    
    # Store emotion data if user_id is provided
    if request.user_id:
        # Create emotion record
        emotion_record = EmotionRecord(
            user_id=request.user_id,
            primary_emotion=emotion_data["primary_emotion"],
            primary_intensity=emotion_data["primary_intensity"],
            confidence=emotion_data["confidence"],
            sentiment_polarity=emotion_data["sentiment"]["polarity"],
            sentiment_subjectivity=emotion_data["sentiment"]["subjectivity"],
            detection_method=emotion_data["method_used"],
            source_text=request.text,
            source_type=request.source_type
        )
        
        # Save to database
        db.add(emotion_record)
        db.commit()
        db.refresh(emotion_record)
    
    # Get appropriate response for the emotion
    response_text = emotion_engine.get_response_for_emotion(
        emotion_data["primary_emotion"],
        emotion_data["primary_intensity"]
    )
    
    # Return emotion data with response
    return {
        "primary_emotion": emotion_data["primary_emotion"],
        "primary_intensity": emotion_data["primary_intensity"],
        "confidence": emotion_data["confidence"],
        "sentiment": emotion_data["sentiment"],
        "response_text": response_text
    }

@router.get("/history/{user_id}", response_model=List[EmotionResponse])
async def get_emotion_history(
    user_id: int,
    limit: int = 10,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get emotion history for a user
    """
    # Query emotion records
    emotion_records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).order_by(
        EmotionRecord.timestamp.desc()
    ).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for record in emotion_records:
        result.append({
            "primary_emotion": record.primary_emotion,
            "primary_intensity": record.primary_intensity,
            "confidence": record.confidence,
            "sentiment": {
                "polarity": record.sentiment_polarity,
                "subjectivity": record.sentiment_subjectivity
            },
            "timestamp": record.timestamp,
            "source_type": record.source_type
        })
    
    return result

@router.get("/insights/{user_id}", response_model=EmotionInsightResponse)
async def get_emotion_insights(
    user_id: int,
    time_period: str = "week",
    db: Session = Depends(get_db)
):
    """
    Get emotion insights for a user over a time period
    """
    # Determine date range
    now = datetime.utcnow()
    if time_period == "day":
        start_date = now - timedelta(days=1)
    elif time_period == "week":
        start_date = now - timedelta(days=7)
    elif time_period == "month":
        start_date = now - timedelta(days=30)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time period. Must be 'day', 'week', or 'month'."
        )
    
    # Query emotion records in the date range
    emotion_records = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id,
        EmotionRecord.timestamp >= start_date
    ).all()
    
    if not emotion_records:
        return {
            "time_period": time_period,
            "dominant_emotion": None,
            "emotion_distribution": {},
            "insight_text": "Not enough data to generate insights yet."
        }
    
    # Calculate emotion distribution
    emotion_counts = {}
    for record in emotion_records:
        emotion = record.primary_emotion
        if emotion in emotion_counts:
            emotion_counts[emotion] += 1
        else:
            emotion_counts[emotion] = 1
    
    # Calculate percentages
    total_records = len(emotion_records)
    emotion_distribution = {
        emotion: count / total_records
        for emotion, count in emotion_counts.items()
    }
    
    # Determine dominant emotion
    dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
    
    # Generate or retrieve insight
    existing_insight = db.query(EmotionInsight).filter(
        EmotionInsight.user_id == user_id,
        EmotionInsight.time_period == time_period,
        EmotionInsight.generated_at >= now - timedelta(hours=12)  # Refresh insights every 12 hours
    ).first()
    
    if existing_insight:
        insight_text = existing_insight.insight_text
    else:
        # Generate new insight
        if dominant_emotion == EmotionCategory.HAPPY:
            insight_text = f"You've been feeling mostly positive during this {time_period}. Keep up the good energy!"
        elif dominant_emotion == EmotionCategory.SAD:
            insight_text = f"You've been experiencing some sadness this {time_period}. Remember to be gentle with yourself."
        elif dominant_emotion == EmotionCategory.ANGRY:
            insight_text = f"You've expressed frustration during this {time_period}. Consider what might help release some tension."
        elif dominant_emotion == EmotionCategory.ANXIOUS:
            insight_text = f"Anxiety has been present for you this {time_period}. Small mindfulness practices might help."
        elif dominant_emotion == EmotionCategory.STRESSED:
            insight_text = f"This {time_period} has brought some stress. Remember to take breaks and prioritize self-care."
        elif dominant_emotion == EmotionCategory.CONFUSED:
            insight_text = f"You've experienced uncertainty this {time_period}. Breaking things down into smaller steps might help."
        elif dominant_emotion == EmotionCategory.MOTIVATED:
            insight_text = f"You've shown great motivation this {time_period}! Channel this energy into your priorities."
        else:
            insight_text = f"Your emotions have been balanced this {time_period}."
        
        # Store the new insight
        new_insight = EmotionInsight(
            user_id=user_id,
            time_period=time_period,
            insight_text=insight_text,
            dominant_emotion=dominant_emotion,
            emotion_distribution=json.dumps(emotion_distribution)
        )
        db.add(new_insight)
        db.commit()
    
    return {
        "time_period": time_period,
        "dominant_emotion": dominant_emotion,
        "emotion_distribution": emotion_distribution,
        "insight_text": insight_text
    }

@router.get("/mood-ring/{user_id}")
async def get_mood_ring(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current mood ring color and status for a user
    """
    # Get most recent emotion record
    latest_emotion = db.query(EmotionRecord).filter(
        EmotionRecord.user_id == user_id
    ).order_by(
        EmotionRecord.timestamp.desc()
    ).first()
    
    if not latest_emotion:
        return {
            "color": "#7F7F7F",  # Neutral gray
            "emotion": "neutral",
            "intensity": "medium",
            "last_updated": None
        }
    
    # Map emotions to colors
    emotion_colors = {
        EmotionCategory.HAPPY: "#FFD700",      # Gold
        EmotionCategory.SAD: "#4169E1",        # Royal Blue
        EmotionCategory.ANGRY: "#FF4500",      # Red-Orange
        EmotionCategory.ANXIOUS: "#9932CC",    # Purple
        EmotionCategory.STRESSED: "#FF6347",   # Tomato
        EmotionCategory.CONFUSED: "#20B2AA",   # Light Sea Green
        EmotionCategory.MOTIVATED: "#32CD32",  # Lime Green
        EmotionCategory.NEUTRAL: "#7F7F7F"     # Gray
    }
    
    # Get color for emotion
    color = emotion_colors.get(latest_emotion.primary_emotion, "#7F7F7F")
    
    return {
        "color": color,
        "emotion": latest_emotion.primary_emotion,
        "intensity": latest_emotion.primary_intensity,
        "last_updated": latest_emotion.timestamp
    }