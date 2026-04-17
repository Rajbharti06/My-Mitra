"""
Care Layer — The warmth that makes responses feel human.

Two things:
1. CARE INJECTION — a phrase that comes before the response
   to signal genuine presence (not performance)

2. TIMING INTELLIGENCE — human delay profiles
   Instant responses feel robotic. A pause feels like thinking.

"I'm really glad you told me this."
"Hey… I'm here with you."
"That's a lot to carry."

These don't come from intelligence. They come from caring.
"""

import random
import asyncio
from typing import Optional, Dict

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CARE OPENINGS
# Short, genuine. Never performative. Never repeated too often.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CARE_OPENINGS: Dict[str, list] = {
    "sad": [
        "I'm really glad you told me this.",
        "Hey… I hear you.",
        "That's not easy to carry alone.",
        "I'm here.",
        "Thank you for sharing that with me.",
    ],
    "stressed": [
        "Hey… I'm right here with you.",
        "I see you.",
        "That sounds like a lot.",
        "You don't have to handle this alone.",
        "Take a breath. I'm here.",
    ],
    "anxious": [
        "Hey… it's okay.",
        "I hear you. Let's think through this together.",
        "You're not alone in this.",
        "I've got you.",
        "Breathe. I'm here.",
    ],
    "angry": [
        "That's valid. I hear you.",
        "You have every right to feel that.",
        "I'm here. Tell me what happened.",
    ],
    "vulnerable": [
        "I'm really glad you trusted me with this.",
        "It takes courage to say that.",
        "I'm not going anywhere.",
        "I hear you. Really.",
    ],
}

# Probability of injecting a care opening (per emotion)
CARE_PROBABILITY: Dict[str, float] = {
    "sad": 0.70,
    "stressed": 0.55,
    "anxious": 0.65,
    "angry": 0.40,
    "vulnerable": 0.85,
    "default": 0.15,
}

# Don't repeat same opening within a session — track last used
_last_care_used: Dict[int, str] = {}


def get_care_opening(
    emotion: str,
    intensity: str,
    user_id: Optional[int] = None,
    is_vulnerable: bool = False,
) -> Optional[str]:
    """
    Maybe return a care opening phrase to prepend to the response.
    Returns None if care should be silent this time.
    """
    if is_vulnerable:
        category = "vulnerable"
    elif emotion in CARE_OPENINGS:
        category = emotion
    else:
        if random.random() > CARE_PROBABILITY["default"]:
            return None
        return None

    prob = CARE_PROBABILITY.get(category, 0.3)
    if intensity == "high":
        prob = min(prob + 0.2, 0.9)
    elif intensity == "low":
        prob *= 0.5

    if random.random() > prob:
        return None

    options = CARE_OPENINGS[category]

    # Avoid repeating last used phrase for this user
    if user_id is not None:
        last = _last_care_used.get(user_id)
        filtered = [o for o in options if o != last]
        chosen = random.choice(filtered) if filtered else random.choice(options)
    else:
        chosen = random.choice(options)

    if user_id is not None:
        _last_care_used[user_id] = chosen

    return chosen


def inject_care(
    response: str,
    emotion: str,
    intensity: str,
    user_id: Optional[int] = None,
    is_vulnerable: bool = False,
) -> tuple[str, Optional[str]]:
    """
    Inject care opening into the response if appropriate.

    Returns:
        (modified_response, care_phrase_used)
        care_phrase_used is None if no care was injected
    """
    phrase = get_care_opening(emotion, intensity, user_id, is_vulnerable)
    if not phrase:
        return response, None

    # Care opening becomes its own line, separated from response
    modified = f"{phrase}\n\n{response}"
    return modified, phrase


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIMING INTELLIGENCE
# Human-paced delays that create genuine presence
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def human_thinking_pause(emotion: str, intensity: str) -> None:
    """
    Wait before starting to respond.
    Instant responses feel robotic.
    A pause says: "I'm actually thinking about what you said."
    """
    if emotion in ("sad", "anxious"):
        delay = random.uniform(1.2, 2.0)
    elif emotion in ("stressed",):
        delay = random.uniform(0.8, 1.4)
    elif emotion in ("angry",):
        delay = random.uniform(0.6, 1.0)
    elif emotion in ("happy", "motivated"):
        delay = random.uniform(0.3, 0.6)
    else:
        delay = random.uniform(0.4, 0.9)

    if intensity == "high":
        delay *= 1.3
    elif intensity == "low":
        delay *= 0.7

    await asyncio.sleep(delay)


async def care_moment_pause() -> None:
    """
    A brief pause after a care opening phrase.
    The silence after "I'm here" is as important as the words.
    """
    await asyncio.sleep(random.uniform(0.4, 0.7))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFLECTION TRIGGERS
# Rare moments where Mitra surfaces a growth reflection
# "You handled that so much better than last time."
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFLECTION_PROBABILITY = 0.04  # ~4% — very rare, very powerful

REFLECTION_PHRASES = [
    "You've actually handled things better this week… I can feel it.",
    "You've come a long way from where this conversation started.",
    "Something's different about how you're talking about this. It's good.",
    "I remember when this felt impossible to you. Look at where you are now.",
    "You don't give yourself enough credit for how far you've come.",
    "There's a quieter confidence in how you're carrying this now.",
]


def maybe_add_reflection(
    response: str,
    days_together: int,
    milestone_count: int,
    current_emotion: str,
) -> tuple[str, bool]:
    """
    Occasionally append a rare growth reflection at the end.
    Only when there's actual history (days > 7, milestones > 1).
    Returns (modified_response, did_reflect).
    """
    if days_together < 7 or milestone_count < 1:
        return response, False

    if current_emotion in ("sad", "anxious", "stressed"):
        return response, False  # Don't do this during hard moments

    if random.random() > REFLECTION_PROBABILITY:
        return response, False

    reflection = random.choice(REFLECTION_PHRASES)
    modified = response.rstrip() + "\n\n" + reflection
    return modified, True
