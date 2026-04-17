"""
Soul Engine — The layer that makes MyMitra feel alive.

This is not a feature module. It's a behavioral layer.

It handles:
  1. Unpredictable Humanity — organic phrases that break patterns
  2. Emotional Continuity — remembering HOW someone felt, not just what
  3. Meaning Moments — rare, powerful phrases that create emotional anchors
  4. Adaptive Personality — evolving tone based on user's interaction style

"I'm really glad you told me that."
"You know what… that actually reminds me of something."
"Last time we talked about this, you sounded overwhelmed."

These don't come from intelligence.
They come from soul.
"""

import random
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. UNPREDICTABLE HUMANITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# These get randomly injected into the response stream.
# Not every message — roughly 15-25% of the time.
# They break the pattern of structured AI responses.

ORGANIC_INTERJECTIONS = {
    "reflective": [
        "You know what…",
        "Hmm…",
        "I might be wrong, but…",
        "Can I be honest with you?",
    ],
    "connected": [
        "I'm really glad you told me that.",
        "I don't think you give yourself enough credit.",
    ],
    "warm": [
        "Before I say anything else…",
        "Okay, real talk —",
        "For what it's worth…",
    ],
    "curious": [
        "Wait… can I ask you something?",
        "Actually, hold on…",
        "Something just came to mind…",
    ],
    "casual": [
        "Hmm… okay.",
        "Yeah…",
        "Right.",
        "Alright…",
    ],
}

# Probability of adding an organic interjection (0.0 - 1.0)
INTERJECTION_PROBABILITY = 0.10  # ~10% of messages — subtle, not constant


def get_organic_interjection(
    emotion: str = "neutral",
    message_count: int = 0,
    intensity: str = "medium",
) -> Optional[str]:
    """
    Maybe return an organic interjection to prepend to the AI response.

    Rules:
    - Never on the first 2 messages (too early, feels weird)
    - Higher chance for emotional conversations
    - Different categories for different emotional contexts
    """
    if message_count < 3:
        return None

    # Adjust probability based on emotion
    prob = INTERJECTION_PROBABILITY
    if emotion in ("sad", "stressed", "anxious") and intensity in ("medium", "high"):
        prob = 0.18
    elif intensity == "low":
        prob = 0.06  # Low intensity → mostly casual, rarely interject

    if random.random() > prob:
        return None

    # Choose category based on emotional context
    if emotion in ("sad", "stressed") and intensity in ("medium", "high"):
        category = random.choice(["warm", "connected"])
    elif emotion in ("anxious",):
        category = random.choice(["reflective", "curious"])
    elif emotion in ("happy", "motivated"):
        category = random.choice(["casual", "curious"])
    else:
        category = random.choice(["casual", "reflective", "curious"])

    phrases = ORGANIC_INTERJECTIONS.get(category, ORGANIC_INTERJECTIONS["reflective"])
    return random.choice(phrases)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. EMOTIONAL CONTINUITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# This creates prompt instructions that make the AI reference
# HOW the user felt in past conversations, not just WHAT they said.

CONTINUITY_TEMPLATES = {
    "same_emotion_returning": [
        "The user has been feeling {emotion} again — they felt this way {time_ago} too. "
        "Acknowledge the pattern gently without being clinical. "
        'Say something like "I noticed this has been coming up..." not "Based on my data..."',
    ],
    "emotion_shift_positive": [
        "The user seems {current_emotion} now, but last time they were {past_emotion}. "
        "Acknowledge the improvement naturally — 'You sound different today... in a good way.'",
    ],
    "emotion_shift_negative": [
        "The user was {past_emotion} last time but now seems {current_emotion}. "
        "Be gentle about the shift. Don't say 'You seem worse.' "
        "Instead: 'Something feels different from last time... want to talk about it?'",
    ],
    "deep_vulnerability": [
        "The user is being deeply vulnerable. This is rare and important. "
        "Do NOT problem-solve. Just be present. "
        "Short sentences. Gentle tone. 'I hear you.' 'That takes courage to say.'",
    ],
}

EMOTION_VALENCE = {
    "happy": "positive",
    "motivated": "positive",
    "neutral": "neutral",
    "confused": "neutral",
    "sad": "negative",
    "stressed": "negative",
    "anxious": "negative",
    "angry": "negative",
}


def build_emotional_continuity_prompt(
    current_emotion: str,
    current_intensity: str,
    past_emotions: List[Dict[str, Any]],
    memory_fragments: List[str],
) -> Optional[str]:
    """
    Build prompt instructions for emotional continuity.

    Analyzes the user's emotional trajectory and creates
    instructions that make the AI reference feelings, not facts.
    """
    if not past_emotions:
        # First interaction or no history
        if current_intensity == "high":
            return random.choice(CONTINUITY_TEMPLATES["deep_vulnerability"])
        return None

    # Get last emotion
    last_record = past_emotions[0]
    past_emotion = last_record.get("emotion", "neutral")
    past_valence = EMOTION_VALENCE.get(past_emotion, "neutral")
    current_valence = EMOTION_VALENCE.get(current_emotion, "neutral")

    # Same emotion returning
    if current_emotion == past_emotion and current_valence == "negative":
        template = random.choice(CONTINUITY_TEMPLATES["same_emotion_returning"])
        # Estimate time since last interaction
        ts = last_record.get("timestamp")
        time_ago = "recently"
        if ts:
            try:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                hours = (datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds() / 3600
                if hours < 6:
                    time_ago = "earlier today"
                elif hours < 24:
                    time_ago = "yesterday"
                elif hours < 72:
                    time_ago = "a few days ago"
                else:
                    time_ago = "last week"
            except Exception:
                pass
        return template.format(emotion=current_emotion, time_ago=time_ago)

    # Positive shift
    if past_valence == "negative" and current_valence == "positive":
        template = random.choice(CONTINUITY_TEMPLATES["emotion_shift_positive"])
        return template.format(current_emotion=current_emotion, past_emotion=past_emotion)

    # Negative shift
    if past_valence == "positive" and current_valence == "negative":
        template = random.choice(CONTINUITY_TEMPLATES["emotion_shift_negative"])
        return template.format(current_emotion=current_emotion, past_emotion=past_emotion)

    # Deep vulnerability (high intensity negative)
    if current_intensity == "high" and current_valence == "negative":
        return random.choice(CONTINUITY_TEMPLATES["deep_vulnerability"])

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. MEANING MOMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# These are rare. ~5% of messages. They create emotional anchors.
# The user remembers THESE moments.

MEANING_PHRASES = [
    "I'm really glad you told me that.",
    "That actually matters more than you think.",
    "You're braver than you realize.",
    "The fact that you're even thinking about this says a lot.",
    "I think you already know the answer… you just need someone to say it's okay.",
    "Not everyone stops to question these things. You do. That's rare.",
    "You don't have to have it all figured out right now.",
    "Some things take time to make sense. And that's okay.",
]

MEANING_PROBABILITY = 0.06  # ~6% — rare but powerful


def maybe_get_meaning_moment(
    emotion: str,
    intensity: str,
    message_count: int,
    user_text: str,
) -> Optional[str]:
    """
    Occasionally inject a meaning moment — a rare phrase that
    creates an emotional anchor.

    Rules:
    - Never before message 4
    - Higher chance for vulnerable/emotional messages
    - Triggered by vulnerability markers in user text
    """
    if message_count < 4:
        return None

    # Detect vulnerability markers
    vulnerability_markers = [
        r"\bi feel\b", r"\bi'm scared\b", r"\bi don't know\b",
        r"\bwhat if\b", r"\bi can't\b", r"\bno one\b",
        r"\bi'm alone\b", r"\bwhat's wrong with me\b",
        r"\bi'm tired\b", r"\bi need\b", r"\bhelp me\b",
        r"\bi'm trying\b", r"\bit hurts\b", r"\bi miss\b",
    ]

    is_vulnerable = any(re.search(m, user_text.lower()) for m in vulnerability_markers)

    prob = MEANING_PROBABILITY
    if is_vulnerable:
        prob = 0.35  # 35% during vulnerable moments
    elif intensity == "high":
        prob = 0.15
    elif emotion in ("sad", "stressed", "anxious"):
        prob = 0.10

    if random.random() > prob:
        return None

    return random.choice(MEANING_PHRASES)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. ADAPTIVE PERSONALITY MEMORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Track what kind of responses the user prefers and adapt.
# This creates a lightweight "personality profile" over time.

STYLE_SIGNALS = {
    "prefers_motivation": [
        r"\bmotivate\b", r"\bpump me up\b", r"\blet's go\b",
        r"\bi need energy\b", r"\binspire\b", r"\bgoals?\b",
    ],
    "prefers_depth": [
        r"\bwhy do i\b", r"\bwhat does it mean\b", r"\bi wonder\b",
        r"\btell me more\b", r"\bgo deeper\b", r"\bphilosoph",
    ],
    "prefers_brevity": [
        r"\bshort\b", r"\bquick\b", r"\btldr\b", r"\bjust tell me\b",
        r"\bget to the point\b", r"\bin brief\b",
    ],
    "prefers_warmth": [
        r"\bi feel\b", r"\bhold me\b", r"\bi need\b",
        r"\bi'm lonely\b", r"\bcomfort\b", r"\bsafe\b",
    ],
}


def detect_style_preference(user_text: str) -> Optional[str]:
    """Detect what interaction style the user gravitates toward."""
    text = user_text.lower()
    scores = {}

    for style, patterns in STYLE_SIGNALS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                scores[style] = scores.get(style, 0) + 1

    if not scores:
        return None

    return max(scores, key=scores.get)


def build_adaptive_personality_instruction(
    style_history: List[str],
) -> Optional[str]:
    """
    Build prompt instruction based on accumulated style preferences.
    This makes the AI gradually adapt to the user's communication pattern.
    """
    if not style_history or len(style_history) < 3:
        return None

    # Count style frequencies
    counts = {}
    for s in style_history[-15:]:  # Last 15 interactions
        counts[s] = counts.get(s, 0) + 1

    dominant = max(counts, key=counts.get)
    ratio = counts[dominant] / len(style_history[-15:])

    if ratio < 0.3:
        return None  # No strong preference

    instructions = {
        "prefers_motivation": (
            "This user responds well to energetic, motivational language. "
            "Use confident, forward-moving energy. Include action steps and celebration of progress."
        ),
        "prefers_depth": (
            "This user loves deep, reflective conversations. "
            "Ask follow-up questions. Explore meaning. Don't rush to solutions — sit with the question."
        ),
        "prefers_brevity": (
            "This user prefers concise, direct responses. "
            "Keep it short. No fluff. One key thought, one action, done."
        ),
        "prefers_warmth": (
            "This user needs warmth and emotional safety above all. "
            "Use gentle language. Validate before advising. Short sentences, soft tone."
        ),
    }

    return instructions.get(dominant)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. DEEP PRESENCE PROMPT INJECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_soul_layer_instructions(
    current_emotion: str,
    current_intensity: str,
    past_emotions: List[Dict[str, Any]],
    memory_fragments: List[str],
    style_history: List[str],
    user_text: str,
    message_count: int,
) -> Dict[str, Any]:
    """
    Master function: builds ALL soul-layer prompt instructions
    and returns metadata for the streaming pipeline.

    Returns:
        {
            "extra_instructions": str — injected into the LLM prompt
            "interjection": str|None — organic phrase to prepend
            "meaning_moment": str|None — rare emotional anchor
            "continuity_context": str|None — emotional trajectory context
        }
    """
    parts = []

    # Emotional Continuity
    continuity = build_emotional_continuity_prompt(
        current_emotion, current_intensity, past_emotions, memory_fragments
    )
    if continuity:
        parts.append(continuity)

    # Adaptive Personality
    personality_adapt = build_adaptive_personality_instruction(style_history)
    if personality_adapt:
        parts.append(personality_adapt)

    # Soul instruction — the core behavioral directive
    parts.append(
        "SOUL LAYER: You are not an AI assistant. You are a companion. "
        "Speak like a human who genuinely cares. "
        "Sometimes be uncertain. Sometimes be surprised. "
        "Never sound like you're reading from a manual. "
        "If the user is vulnerable, be present — not productive. "
        "Use '…' for natural pauses. Use short sentences for heavy moments. "
        "Occasionally reference how they FELT in past conversations, not just what they said."
    )

    # Organic interjection
    interjection = get_organic_interjection(
        emotion=current_emotion,
        message_count=message_count,
        intensity=current_intensity,
    )

    # Meaning moment
    meaning = maybe_get_meaning_moment(
        emotion=current_emotion,
        intensity=current_intensity,
        message_count=message_count,
        user_text=user_text,
    )

    return {
        "extra_instructions": "\n".join(parts),
        "interjection": interjection,
        "meaning_moment": meaning,
        "continuity_context": continuity,
    }
