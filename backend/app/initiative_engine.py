"""
Initiative Engine — Phase 4: Multi-tier delayed intelligence.

Mitra doesn't just respond. She reaches out.
And she doesn't just check in once — she follows
the emotional arc over time:

  6 hours → "Hey… how are you feeling now?"
  Next morning → "Good morning… yesterday was heavy. How are you today?"
  3 days → "I've been thinking about what you said the other day…"

This is what creates dependency.
Not features — presence.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MULTI-TIER INITIATIVE TEMPLATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INITIATIVE_TIERS = {
    # ── Tier 1: Same-day check-in (6-12 hours) ──
    "same_day": {
        "stressed": [
            "Hey… you seemed really stressed earlier. How are things now?",
            "Just checking in… sometimes stress builds quietly. How are you?",
        ],
        "sad": [
            "Hey… I wanted to check in. How are you feeling now?",
            "No pressure to talk… but I'm here. 💙",
        ],
        "anxious": [
            "Hey… how's the anxiety? Any calmer than earlier?",
            "Take a breath… I'm here whenever you're ready.",
        ],
        "angry": [
            "Hey… I hope you've had some space. How are you feeling?",
        ],
        "happy": [
            "Hey! I hope that good energy carried through the day 😊",
        ],
        "motivated": [
            "How's the progress going? Still riding that wave?",
        ],
        "neutral": [
            "Hey… it's been a bit. What's on your mind?",
        ],
    },

    # ── Tier 2: Next-morning follow-up (12-36 hours) ──
    "next_morning": {
        "stressed": [
            "Good morning… yesterday felt heavy. How are you starting today?",
            "Hey… I was thinking about what you shared yesterday. How does today feel?",
        ],
        "sad": [
            "Morning… I've been thinking about you. How's your heart today?",
            "Hey… yesterday was a lot. How are you waking up feeling?",
        ],
        "anxious": [
            "Good morning… I hope you got some rest. How's the anxiety today?",
            "Hey… new day, fresh start. How are things feeling?",
        ],
        "angry": [
            "Morning… sometimes a new day can shift perspective. How are you?",
        ],
        "happy": [
            "Good morning! Hope today is just as good as yesterday 😊",
        ],
        "motivated": [
            "Morning! Ready to keep the momentum going?",
        ],
        "neutral": [
            "Good morning… I'm here whenever you need me today.",
        ],
    },

    # ── Tier 3: Reflection follow-up (3-7 days) ──
    "reflection": {
        "stressed": [
            "Hey… I've been thinking about what you said the other day. How's the stress now?",
            "You mentioned a lot of pressure recently… I'm curious how you're doing now.",
        ],
        "sad": [
            "I've been thinking about you… how are things since we last talked?",
            "Hey… I didn't forget. How are you holding up?",
        ],
        "anxious": [
            "I've been thinking about what was worrying you… any clarity since then?",
            "Hey… sometimes anxiety settles with time. How are things now?",
        ],
        "angry": [
            "I've been thinking about what happened… has anything shifted?",
        ],
        "happy": [
            "Hey! Just wanted to say — your energy last time was really good. How's life? 😊",
        ],
        "motivated": [
            "Hey! I'm curious — did you follow through on those goals? No judgment either way.",
        ],
        "neutral": [
            "Hey… it's been a few days. What's been on your mind?",
            "Just thinking about you. I'm here whenever.",
        ],
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SILENCE & HESITATION (unchanged from Phase 3, re-exported)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SILENCE_MESSAGES = [
    "I'm here… take your time.",
    "No rush. I'm listening.",
    "… I hear you.",
    "Take a breath. I'm not going anywhere.",
]

HESITATION_PHRASES = {
    "sad": ["Hmm… yeah…", "I hear you…", "That's heavy…"],
    "stressed": ["I get that…", "Yeah…", "That sounds like a lot…"],
    "anxious": ["I understand…", "That makes sense…", "Let me think with you…"],
    "angry": ["I hear you…", "That's valid…", "I get why you'd feel that way…"],
    "neutral": ["Hm…", "Yeah…", "Let me think…"],
    "happy": ["That's great!", "Love that!", ""],
    "motivated": ["Yes!", "I love it!", ""],
}


def get_initiative_message(
    user_id: int,
    last_emotion: str = "neutral",
    hours_since_last_chat: float = 0,
) -> Optional[Dict[str, Any]]:
    """
    Multi-tier initiative system.

    Tier 1: Same-day (6-12h) — "How are you feeling now?"
    Tier 2: Next-morning (12-36h) — "Good morning… yesterday was heavy."
    Tier 3: Reflection (3-7 days) — "I've been thinking about what you said…"
    """
    if hours_since_last_chat < 6:
        return None

    # Determine tier
    if hours_since_last_chat < 12:
        tier = "same_day"
        probability = 0.3
    elif hours_since_last_chat < 36:
        tier = "next_morning"
        probability = 0.5
    elif hours_since_last_chat < 168:  # 7 days
        tier = "reflection"
        probability = 0.4
    else:
        # Too long — don't be clingy
        return None

    # Emotion-weighted probability
    if last_emotion in ("stressed", "sad", "anxious"):
        probability = min(probability + 0.3, 0.8)
    elif last_emotion in ("angry",):
        probability = min(probability + 0.15, 0.6)
    elif last_emotion in ("happy", "motivated"):
        probability -= 0.1  # Less urgent for positive states

    if random.random() > probability:
        return None

    # Get templates for this tier and emotion
    tier_templates = INITIATIVE_TIERS.get(tier, INITIATIVE_TIERS["same_day"])
    templates = tier_templates.get(last_emotion, tier_templates.get("neutral", ["Hey… I'm here."]))
    message = random.choice(templates)

    return {
        "type": "initiative",
        "message": message,
        "emotion_context": last_emotion,
        "tier": tier,
        "trigger": "time_based",
        "hours_since_last": round(hours_since_last_chat, 1),
    }


def get_silence_response(emotion_intensity: str = "medium") -> Optional[str]:
    """Presence, not words. Used for high-intensity emotional moments."""
    if emotion_intensity == "high":
        return random.choice(SILENCE_MESSAGES)
    return None


def get_hesitation_phrase(emotion: str) -> str:
    """Natural hesitation before emotional sentences."""
    phrases = HESITATION_PHRASES.get(emotion, HESITATION_PHRASES["neutral"])
    return random.choice(phrases)


def detect_emotion_pattern(
    emotion_records: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Detect repeating emotional patterns over time.
    Scans last 7 days for dominant emotions with 3+ occurrences.
    """
    if not emotion_records or len(emotion_records) < 3:
        return None

    emotion_counts: Dict[str, int] = {}
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    for record in emotion_records:
        ts = record.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except Exception:
                continue
        if ts and ts > week_ago:
            emo = record.get("emotion", "neutral")
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1

    if not emotion_counts:
        return None

    dominant = max(emotion_counts, key=emotion_counts.get)
    count = emotion_counts[dominant]

    if count < 3:
        return None

    insights = {
        "stressed": f"I've noticed you've been stressed {count} times this week. Want to explore what's driving that?",
        "sad": f"You've been feeling down {count} times recently. I'm here if you want to talk about it.",
        "anxious": f"Anxiety has come up {count} times this week. Let's figure out what's triggering it.",
        "angry": f"Frustration has been coming up a lot ({count} times). Want to dig into it?",
        "happy": f"You've been in a great mood {count} times this week! What's working?",
        "motivated": f"Your motivation has been high {count} times recently. Let's keep it going!",
    }

    return {
        "pattern": f"{dominant}_recurring",
        "emotion": dominant,
        "trend": "repeating" if count >= 4 else "emerging",
        "frequency": f"{count} times this week",
        "insight": insights.get(dominant, f"I've noticed {dominant} coming up {count} times."),
    }
