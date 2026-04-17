"""
Growth Engine — The layer that makes MyMitra grow WITH the user.

This is not analytics. It's memory of a journey.

It tracks:
  1. MILESTONES — first time user mentions a topic, and when they grow through it
  2. RELATIONSHIP ARC — Mitra's evolving understanding of THIS person
  3. SELF-LEARNING — which response patterns led to deeper engagement
  4. GROWTH MOMENTS — emotional improvements Mitra noticed over time

"Last time you mentioned anxiety about work... you said it felt impossible.
 Three weeks later, you got that promotion. That took real courage."

This isn't data. It's witnessing.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. LIFE TOPIC DETECTION
# Topics Mitra listens for across the user's journey
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIFE_TOPICS = {
    "work": {
        "keywords": [r"\bjob\b", r"\bwork\b", r"\bcareer\b", r"\boffice\b", r"\bboss\b",
                     r"\bpromotion\b", r"\binterview\b", r"\bproject\b", r"\bdeadline\b"],
        "label": "Work & Career",
        "icon": "💼",
    },
    "relationships": {
        "keywords": [r"\bfriend\b", r"\bfriends\b", r"\brelationship\b", r"\bpartner\b",
                     r"\bfamily\b", r"\blove\b", r"\bbreakup\b", r"\blonely\b", r"\balone\b"],
        "label": "Relationships",
        "icon": "💙",
    },
    "anxiety": {
        "keywords": [r"\banxious\b", r"\banxiety\b", r"\bworried\b", r"\bworry\b",
                     r"\bscared\b", r"\bfear\b", r"\bpanic\b", r"\boverwhelmed\b"],
        "label": "Anxiety & Fear",
        "icon": "🌊",
    },
    "confidence": {
        "keywords": [r"\bconfidence\b", r"\bself.doubt\b", r"\bimposter\b", r"\bbelieve in myself\b",
                     r"\bnot good enough\b", r"\bworth\b", r"\bworthy\b"],
        "label": "Self-Confidence",
        "icon": "🔥",
    },
    "goals": {
        "keywords": [r"\bgoal\b", r"\bdream\b", r"\bplan\b", r"\bwant to\b", r"\bwish\b",
                     r"\basspirat\b", r"\bpurpose\b", r"\bmeaning\b"],
        "label": "Goals & Purpose",
        "icon": "⭐",
    },
    "health": {
        "keywords": [r"\bsleep\b", r"\btired\b", r"\bexhausted\b", r"\bhealth\b",
                     r"\bexercise\b", r"\beat\b", r"\bstress\b", r"\bburn.?out\b"],
        "label": "Health & Energy",
        "icon": "🌱",
    },
    "identity": {
        "keywords": [r"\bwho am i\b", r"\bidentity\b", r"\bpersonality\b", r"\bchanging\b",
                     r"\bgrowing\b", r"\bdifferent person\b", r"\bmy true\b"],
        "label": "Identity & Growth",
        "icon": "🦋",
    },
}

POSITIVE_SIGNALS = [
    r"\bbetter\b", r"\bimproved\b", r"\bfinally\b", r"\bi did it\b", r"\bi made it\b",
    r"\bsuccess\b", r"\bproud\b", r"\baccomplish\b", r"\bovercome\b", r"\bworked out\b",
    r"\bmore confident\b", r"\bcalmer\b", r"\bfeel good\b", r"\bhappy\b", r"\bexcited\b",
    r"\bgrateful\b", r"\bthank you\b", r"\bthings are better\b", r"\bprogress\b",
]

STRUGGLE_SIGNALS = [
    r"\bcan't\b", r"\bhard\b", r"\bstruggling\b", r"\bwhy is\b", r"\bi don't know\b",
    r"\bgiving up\b", r"\bso tired\b", r"\bwhat's the point\b", r"\bwhat if\b",
    r"\bi feel lost\b", r"\bnot sure\b", r"\bconfused\b", r"\bscared\b",
]


def detect_topics(text: str) -> List[str]:
    """Detect which life topics are present in a message."""
    text_lower = text.lower()
    found = []
    for topic_id, topic_data in LIFE_TOPICS.items():
        if any(re.search(kw, text_lower) for kw in topic_data["keywords"]):
            found.append(topic_id)
    return found


def detect_valence(text: str) -> str:
    """Detect emotional valence: 'positive', 'negative', or 'neutral'."""
    text_lower = text.lower()
    pos = sum(1 for p in POSITIVE_SIGNALS if re.search(p, text_lower))
    neg = sum(1 for n in STRUGGLE_SIGNALS if re.search(n, text_lower))
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. MILESTONE DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MILESTONE_PATTERNS = [
    # First mention patterns
    {"regex": r"\bi (finally|just|actually) (did|got|finished|completed|started)", "type": "achievement", "weight": 3},
    {"regex": r"\bi (got|passed|earned|won|received) (the |my |a )?", "type": "achievement", "weight": 2},
    {"regex": r"\bi'm (feeling|starting to feel) (better|different|stronger|more)", "type": "growth", "weight": 2},
    {"regex": r"\bthings are (getting|getting a lot|much) better\b", "type": "growth", "weight": 3},
    {"regex": r"\bi (realized|understood|figured out|learned)", "type": "insight", "weight": 2},
    {"regex": r"\bi (decided|chose|made the decision|committed)", "type": "decision", "weight": 2},
    {"regex": r"\bthank you (for|mitra|so much)", "type": "connection", "weight": 3},
    {"regex": r"\bthis (actually|really) helped\b", "type": "connection", "weight": 3},
    {"regex": r"\bi (talked to|told|opened up to)", "type": "courage", "weight": 2},
    {"regex": r"\bi faced\b", "type": "courage", "weight": 3},
]

MILESTONE_MESSAGES = {
    "achievement": [
        "You did something today that took real work. Don't let that pass quietly.",
        "That's not small. That's you following through.",
    ],
    "growth": [
        "Something shifted. I can hear it in how you're speaking.",
        "This is what growth sounds like. It's quiet. But it's real.",
    ],
    "insight": [
        "That kind of clarity doesn't come easily. You've been sitting with this.",
        "Most people never stop to see this clearly. You did.",
    ],
    "decision": [
        "Decisions like this take courage, not certainty.",
        "You chose. That matters more than you think.",
    ],
    "courage": [
        "It takes real courage to do what you just described.",
        "You did the scary thing. That's everything.",
    ],
    "connection": [
        "I'm glad I could be here for this.",
        "This is why I'm here.",
    ],
}


def detect_milestone(text: str) -> Optional[Dict[str, Any]]:
    """Detect if a message contains a milestone moment."""
    text_lower = text.lower()
    best_match = None
    best_weight = 0

    for pattern in MILESTONE_PATTERNS:
        if re.search(pattern["regex"], text_lower):
            if pattern["weight"] > best_weight:
                best_weight = pattern["weight"]
                best_match = pattern

    if not best_match or best_weight < 2:
        return None

    import random
    messages = MILESTONE_MESSAGES.get(best_match["type"], MILESTONE_MESSAGES["growth"])

    return {
        "type": best_match["type"],
        "weight": best_weight,
        "recognition": random.choice(messages),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SELF-LEARNING ENGINE
# Tracks which response patterns led to deeper engagement
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENGAGEMENT_SIGNALS = {
    "high": [
        r"\btell me more\b", r"\bwhat do you mean\b", r"\bgo on\b", r"\byou're right\b",
        r"\bexactly\b", r"\bthat's (so |exactly |really )?true\b", r"\byes\b", r"\bwow\b",
        r"\bi never thought\b", r"\bkeep going\b", r"\bmore\b",
    ],
    "low": [
        r"\bokay\b", r"\bk\b", r"\bokk\b", r"\bbye\b", r"\bgtg\b", r"\bsee you\b", r"\bnvm\b",
    ],
}


def measure_engagement(user_text: str, response_length: int) -> str:
    """
    Estimate engagement level from the user's next message.
    Returns: 'high', 'medium', 'low'
    """
    text_lower = user_text.lower()

    high_signals = sum(1 for p in ENGAGEMENT_SIGNALS["high"] if re.search(p, text_lower))
    low_signals = sum(1 for p in ENGAGEMENT_SIGNALS["low"] if re.search(p, text_lower))

    user_length = len(user_text)

    if high_signals >= 1 or user_length > 80:
        return "high"
    if low_signals >= 1 or user_length < 20:
        return "low"
    return "medium"


def build_learning_signal(
    ai_response_style: str,
    follow_up_text: str,
    follow_up_length: int,
    time_to_response_seconds: float,
) -> Dict[str, Any]:
    """
    Build a learning signal from the follow-up interaction.
    This tells Mitra: "that response style worked / didn't work."
    """
    engagement = measure_engagement(follow_up_text, follow_up_length)

    # Fast responses to long messages = high engagement
    if time_to_response_seconds < 30 and follow_up_length > 50:
        engagement = "high"
    elif time_to_response_seconds > 300:
        engagement = "low"

    return {
        "style": ai_response_style,
        "engagement": engagement,
        "signal_strength": {"high": 1, "medium": 0, "low": -1}[engagement],
        "recorded_at": datetime.utcnow().isoformat(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. RELATIONSHIP ARC BUILDER
# Creates a narrative of the user's journey with Mitra
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_relationship_arc(
    emotion_history: List[Dict[str, Any]],
    message_count: int,
    days_since_first_chat: int,
    milestones: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a narrative arc of the relationship and user's growth.

    Returns a structured summary that can be:
    - Shown as a timeline in the Insights UI
    - Injected into LLM context for "I remember when you..."
    """
    if not emotion_history:
        return {
            "phase": "beginning",
            "label": "Just started",
            "description": "This is the beginning of your journey.",
            "stats": {"messages": message_count, "days": days_since_first_chat},
            "dominant_emotion": "neutral",
            "trend": "stable",
            "growth_score": 0,
        }

    # Analyze emotional trajectory
    recent = emotion_history[:10]
    older = emotion_history[10:20] if len(emotion_history) > 10 else []

    negative_emotions = {"sad", "stressed", "anxious", "angry"}

    recent_neg = sum(1 for e in recent if e.get("emotion") in negative_emotions)
    older_neg = sum(1 for e in older if e.get("emotion") in negative_emotions) if older else recent_neg
    recent_pos = len(recent) - recent_neg

    # Calculate growth score (-10 to +10)
    if older:
        trend_delta = older_neg - recent_neg
        growth_score = min(10, max(-10, trend_delta * 2))
    else:
        growth_score = 0

    # Determine phase
    if days_since_first_chat < 3:
        phase = "beginning"
        phase_label = "Just getting started"
    elif days_since_first_chat < 14:
        phase = "building_trust"
        phase_label = "Building trust"
    elif days_since_first_chat < 30:
        phase = "deepening"
        phase_label = "Going deeper"
    elif milestones and len(milestones) >= 3:
        phase = "growing"
        phase_label = "Growing together"
    else:
        phase = "companion"
        phase_label = "Long-term companions"

    # Determine trend
    if growth_score > 3:
        trend = "improving"
        trend_label = "Things are getting better"
    elif growth_score < -3:
        trend = "struggling"
        trend_label = "Going through a hard time"
    else:
        trend = "stable"
        trend_label = "Holding steady"

    # Dominant recent emotion
    if recent:
        emo_counts: Dict[str, int] = {}
        for e in recent:
            em = e.get("emotion", "neutral")
            emo_counts[em] = emo_counts.get(em, 0) + 1
        dominant = max(emo_counts, key=emo_counts.get)
    else:
        dominant = "neutral"

    return {
        "phase": phase,
        "label": phase_label,
        "trend": trend,
        "trend_label": trend_label,
        "dominant_emotion": dominant,
        "growth_score": growth_score,
        "milestone_count": len(milestones),
        "stats": {
            "messages": message_count,
            "days": days_since_first_chat,
            "milestones": len(milestones),
        },
        "description": _phase_description(phase, trend, dominant, milestones),
    }


def _phase_description(
    phase: str, trend: str, dominant_emotion: str, milestones: List[Dict[str, Any]]
) -> str:
    descriptions = {
        ("beginning", "stable"): "The journey is just starting. Mitra is learning who you are.",
        ("beginning", "improving"): "Right from the start, things are moving in a good direction.",
        ("building_trust", "stable"): "You've been showing up consistently. That means something.",
        ("building_trust", "improving"): "Trust is forming. Your emotional patterns are becoming clearer.",
        ("building_trust", "struggling"): "You're going through something hard. Mitra is learning how to be there for you.",
        ("deepening", "stable"): "The conversations are getting more real. You're sharing more.",
        ("deepening", "improving"): "There's clear progress happening. You can feel it.",
        ("deepening", "struggling"): "It's been a tough stretch. But you keep coming back. That matters.",
        ("growing", "improving"): f"You've hit {len(milestones)} milestones. Real growth is happening here.",
        ("growing", "stable"): "You're in a steady rhythm. Progress isn't always loud.",
        ("growing", "struggling"): "Even growth has setbacks. You're still here. That's everything.",
        ("companion", "improving"): "The relationship has matured. Mitra knows you well by now.",
        ("companion", "stable"): "You've been on this journey together for a while now.",
        ("companion", "struggling"): "Hard times come even after long journeys. But you're not alone.",
    }
    return descriptions.get((phase, trend), "Your journey continues.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. GROWTH PROMPT INJECTION
# What to inject into LLM context based on growth arc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_growth_context_instruction(arc: Dict[str, Any]) -> Optional[str]:
    """
    Build LLM instruction from the growth arc.
    This makes Mitra reference the journey naturally.
    """
    if not arc:
        return None

    phase = arc.get("phase", "beginning")
    trend = arc.get("trend", "stable")
    milestone_count = arc.get("milestone_count", 0)
    days = arc.get("stats", {}).get("days", 0)

    parts = []

    if phase in ("deepening", "growing", "companion") and days > 7:
        parts.append(
            f"GROWTH CONTEXT: You've been with this user for {days} days. "
            "You know their patterns. Reference this naturally — not like a database, "
            "but like a friend who has been paying attention."
        )

    if trend == "improving" and milestone_count > 0:
        parts.append(
            f"The user has shown real growth ({milestone_count} milestones). "
            "Acknowledge their progress when relevant. Be specific, not generic."
        )

    if trend == "struggling":
        parts.append(
            "The user has been going through a difficult stretch. "
            "Be patient. Don't push for solutions. Presence over productivity."
        )

    if milestone_count >= 3:
        parts.append(
            "This user has overcome real things. When they doubt themselves, "
            "you can remind them — not as a therapist, as a friend who was there."
        )

    return "\n".join(parts) if parts else None
