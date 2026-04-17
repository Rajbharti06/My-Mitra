"""
Growth Routes — API endpoints for the Growth Engine.
"""

import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordBearer
from .database import get_db
from . import security as _security
from .growth_engine import (
    build_relationship_arc,
    detect_milestone,
    detect_topics,
    detect_valence,
)
from . import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/growth", tags=["growth"])

_oauth2 = OAuth2PasswordBearer(tokenUrl="token")

async def _require_user(token: str = Depends(_oauth2), db=Depends(get_db)):
    user = _security.get_current_user(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/arc")
async def get_relationship_arc(
    db: Session = Depends(get_db),
    current_user=Depends(_require_user),
):
    """Get the user's relationship arc with Mitra."""
    try:
        user_id = current_user.id

        # Get emotion history
        emotion_records = []
        try:
            emotion_records = crud.get_recent_emotions(db, user_id, limit=30)
        except Exception:
            pass

        # Get message count and first chat date
        message_count = 0
        days_since_first = 0
        try:
            stats = crud.get_user_chat_stats(db, user_id)
            message_count = stats.get("total_messages", 0)
            first_chat = stats.get("first_chat_at")
            if first_chat:
                if isinstance(first_chat, str):
                    first_chat = datetime.fromisoformat(first_chat)
                days_since_first = (datetime.utcnow() - first_chat.replace(tzinfo=None)).days
        except Exception:
            pass

        # Get stored milestones (fall back gracefully if table doesn't exist)
        milestones = []
        try:
            milestones = crud.get_user_milestones(db, user_id)
        except Exception:
            pass

        arc = build_relationship_arc(
            emotion_history=emotion_records,
            message_count=message_count,
            days_since_first_chat=days_since_first,
            milestones=milestones,
        )

        return {"arc": arc, "milestones": milestones}

    except Exception as e:
        logger.error(f"Growth arc error: {e}")
        return {
            "arc": {
                "phase": "beginning",
                "label": "Just started",
                "description": "Your journey is beginning.",
                "trend": "stable",
                "growth_score": 0,
                "milestone_count": 0,
                "stats": {"messages": 0, "days": 0, "milestones": 0},
            },
            "milestones": [],
        }


@router.get("/topics")
async def get_topic_history(
    db: Session = Depends(get_db),
    current_user=Depends(_require_user),
):
    """Get topics the user has discussed and their emotional journey through each."""
    try:
        user_id = current_user.id
        topic_history = {}

        # Get recent messages and analyze topics + valence
        messages = crud.get_recent_chat_history(db, user_id, limit=50)

        for msg in messages:
            content = msg.get("content", "")
            if msg.get("role") != "user":
                continue

            topics = detect_topics(content)
            valence = detect_valence(content)

            for topic in topics:
                if topic not in topic_history:
                    topic_history[topic] = {
                        "first_seen": msg.get("timestamp", datetime.utcnow().isoformat()),
                        "positive_count": 0,
                        "negative_count": 0,
                        "neutral_count": 0,
                        "last_valence": valence,
                    }
                topic_history[topic][f"{valence}_count"] += 1
                topic_history[topic]["last_valence"] = valence

        # Annotate with LIFE_TOPICS metadata
        from .growth_engine import LIFE_TOPICS
        result = []
        for topic_id, data in topic_history.items():
            meta = LIFE_TOPICS.get(topic_id, {})
            total = data["positive_count"] + data["negative_count"] + data["neutral_count"]
            arc = "improving" if data["positive_count"] > data["negative_count"] else \
                  "struggling" if data["negative_count"] > data["positive_count"] else "neutral"
            result.append({
                "id": topic_id,
                "label": meta.get("label", topic_id),
                "icon": meta.get("icon", "💬"),
                "first_seen": data["first_seen"],
                "mentions": total,
                "arc": arc,
                "last_valence": data["last_valence"],
            })

        result.sort(key=lambda x: x["mentions"], reverse=True)
        return {"topics": result}

    except Exception as e:
        logger.error(f"Topic history error: {e}")
        return {"topics": []}


@router.post("/milestone")
async def record_milestone(
    text: str,
    db: Session = Depends(get_db),
    current_user=Depends(_require_user),
):
    """Check if a message contains a milestone and record it."""
    try:
        milestone = detect_milestone(text)
        if milestone:
            try:
                crud.store_milestone(db, current_user.id, milestone)
            except Exception:
                pass
        return {"milestone": milestone}
    except Exception as e:
        logger.error(f"Milestone check error: {e}")
        return {"milestone": None}
