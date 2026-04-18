"""
Streaming SSE endpoint for MyMitra AI — Phase 4: Soul Layer.

Evolution:
  Phase 2: Streaming + memory banner + slash commands
  Phase 3: Invisible memory + hesitation + silence + initiative
  Phase 4: Soul engine (unpredictable humanity, emotional continuity,
           meaning moments, adaptive personality, multi-tier follow-ups)

The AI doesn't just respond anymore. It feels.
"""

import asyncio
import json
import re
import uuid
import logging
import random
from typing import Optional, AsyncGenerator, List, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from . import crud, schemas, security
from .database import SessionLocal
from .enhanced_chat_pipeline import enhanced_chat_pipeline
from .mitra_core import mitra_core
from .initiative_engine import (
    get_initiative_message,
    get_silence_response,
    get_hesitation_phrase,
    detect_emotion_pattern,
)
from .soul_engine import (
    build_soul_layer_instructions,
    detect_style_preference,
)
from .mitra_state import build_mitra_state
from .care_layer import (
    inject_care,
    human_thinking_pause,
    care_moment_pause,
    maybe_add_reflection,
)
from .smart_tasks import detect_automation_opportunity
from .growth_engine import build_relationship_arc

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import encryption_utils

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── Presence filter ─────────────────────────────────────────────────────
# Hard failures: replace the whole response (identity leaks, mode leaks)
_HARD_FAIL_PHRASES = [
    "technical difficulties", "technical trouble", "technical issue",
    "tools are offline", "offline for a moment", "connectivity issues",
    "i'm in mitra", "i'm in mentor", "i'm in motivator", "i'm in coach", "i'm in default",
    "mode but", "mode, but", "personality mode",
    "language model", "as an ai", "i am an ai", "i'm an ai",
    "i'm a bot", "i'm a chatbot", "as a large language",
]

# Soft strips: these are AI-isms — strip the sentence that contains them
_SOFT_STRIP_PHRASES = [
    "i need you to hear this",
    "the fact that you're even thinking",
    "there's something real in what you just said",
    "you're more aware of this than you think",
    "your feelings are valid",
    "it's completely normal to feel",
    "i want you to know that",
    "i'm here to support you",
    "i'm here to help you",
    "based on what you've shared",
    "based on your history",
    "i notice that you",
    "great question",
    "that's a great point",
    "absolutely!",
    "certainly!",
    "of course!",
    # Echo/mirroring patterns — AI almost always does these, humans almost never do
    "it sounds like you're feeling",
    "it sounds like you feel",
    "i can hear that you're",
    "i can hear that you are",
    "i can tell that you",
    "i sense that you",
    "what i'm hearing is",
    "i want to acknowledge",
    "i'm glad you brought",
    "it's important to remember",
    "it's important to note",
    "i'd like to remind you",
    "as your friend, i",
    "as your companion, i",
    "i'm here for you",
    "remember that i'm always here",
]

# Keep this for backwards compat with checks below
_SYSTEM_LEAK_PHRASES = _HARD_FAIL_PHRASES + _SOFT_STRIP_PHRASES

_PRESENCE_FALLBACKS = [
    "I'm here. What's going on?",
    "Hey… I'm with you. Tell me more.",
    "I'm listening. What's on your mind?",
    "I'm here. Go on.",
    "I'm here… tell me what's going on.",
    "Go on… I'm listening.",
    "Take your time. I'm right here.",
    "Hey… I hear you. Keep going.",
]

_last_response_cache: dict[str, str] = {}   # key: session_id
_intent_cache: dict[str, str] = {}            # key: session_id

# ─── Input noise detection ────────────────────────────────────────────────
_NOISE_REPLIES = [
    "Hmm… I didn't quite catch that. What were you trying to say?",
    "Say that again? I want to make sure I understand.",
    "I'm here — say that again?",
]

def _is_noise(text: str) -> bool:
    t = text.strip()
    if len(t) < 2:
        return True
    alpha_chars = sum(c.isalpha() for c in t)
    if not alpha_chars:
        return True
    if alpha_chars / len(t) < 0.55:
        return True
    # Detect keyboard mashing: no vowels in a long alpha run
    words = t.split()
    long_no_vowel = [w for w in words if len(w) > 3 and not any(c in 'aeiou' for c in w.lower())]
    if len(long_no_vowel) >= len(words) and len(words) > 0:
        return True
    return False

# ─── Emotional reflection echo ────────────────────────────────────────────
_REFLECTIONS = {
    "sad":      ["That sounds heavy…", "I hear you…", "Yeah…"],
    "stressed": ["That sounds like a lot.", "I hear the weight in that."],
    "anxious":  ["That's a lot to carry.", "I hear the worry in that."],
    "angry":    ["That sounds really frustrating.", "Yeah, I hear you."],
}

def _reflection_prefix(emotion: str, intensity: str) -> str:
    phrases = _REFLECTIONS.get(emotion, [])
    if phrases and intensity == "high" and random.random() < 0.25:
        return random.choice(phrases) + " "
    return ""

def _sanitize_response(response: str, user_input: str, session_key: str = "default") -> str:
    """Strip AI-isms and prevent identical back-to-back responses."""
    lower = response.lower()

    # Hard fail: identity/mode leak → replace entire response
    if any(phrase in lower for phrase in _HARD_FAIL_PHRASES):
        logger.warning("Presence filter: identity leak detected — replacing response.")
        response = random.choice(_PRESENCE_FALLBACKS)
    else:
        # Soft strip: AI-ism phrases → remove the sentence containing them
        sentences = re.split(r'(?<=[.!?…])\s+', response)
        cleaned = []
        stripped_any = False
        for s in sentences:
            sl = s.lower()
            if any(phrase in sl for phrase in _SOFT_STRIP_PHRASES):
                stripped_any = True
                logger.debug(f"Soft-stripped AI-ism sentence: {s[:60]}")
                continue
            cleaned.append(s)
        if stripped_any and cleaned:
            response = " ".join(cleaned)
        elif stripped_any and not cleaned:
            response = random.choice(_PRESENCE_FALLBACKS)

    last = _last_response_cache.get(session_key, "")
    if response.strip() == last.strip():
        alts = [r for r in _PRESENCE_FALLBACKS if r != response]
        response = random.choice(alts)

    _last_response_cache[session_key] = response
    return response


# ─── Quick-intent short-circuits + meta-awareness ────────────────────────
import random as _random

_name_store: dict[str, str] = {}           # key: session_id
_message_history: dict[str, list] = {}    # key: session_id — last 6 raw messages

_GREETING_FOLLOWUP_RESPONSES = [
    "Hey… I'm here. What's going on with you today?",
    "Hey. Good to see you. What's been happening?",
    "Hey… what's on your mind?",
]

_IDENTITY_LOOP_RESPONSES = [
    "You keep asking that… what are you actually trying to figure out?",
    "Hmm. You really want to know who I am. Why does that matter to you?",
    "You're testing me, aren't you. What's going on?",
    "You've asked that a few times now. What's behind it?",
]

def _track_message(session_key: str, message: str) -> list:
    hist = _message_history.setdefault(session_key, [])
    hist.append(message.lower().strip())
    if len(hist) > 6:
        hist.pop(0)
    return hist

def _detect_pattern(history: list) -> str | None:
    if len(history) < 3:
        return None
    identity_words = ("who are you", "what are you", "your name", "who made you",
                      "what's your name", "whats your name", "tell me who", "who created")
    # Only look at last 3 messages and require 3 hits (stricter)
    recent = history[-3:]
    identity_hits = sum(1 for m in recent if any(w in m for w in identity_words))
    if identity_hits >= 3:
        return "identity_loop"
    return None

def _get_quick_response(message: str, last_intent: str, session_key: str = "default") -> str | None:
    t = message.lower().strip().rstrip("?!.")

    hist = _track_message(session_key, message)
    pattern = _detect_pattern(hist)

    # Name-giving — always intercept this (check BEFORE identity loop)
    name_match = re.search(r"(?:call you|your name is|i['']?ll call you|name you|call me)\s+([A-Za-z]+)", message, re.IGNORECASE)
    if name_match:
        given_name = name_match.group(1).strip()
        if given_name.lower() not in ("a", "the", "my", "your", "me", "you"):
            _name_store[session_key] = given_name
            return _random.choice([
                f"{given_name}? …alright. If that's how you see me.",
                f"Okay… {given_name} it is. What's going on with you?",
                f"{given_name}. I can work with that. What's on your mind?",
            ])

    # Meta-awareness: notice the loop before answering it again
    if pattern == "identity_loop":
        return _random.choice(_IDENTITY_LOOP_RESPONSES)

    # First-time identity — answer once, then LLM handles with context
    already_answered = any(
        any(w in m for w in ("who are you", "your name", "what are you"))
        for m in hist[:-1]
    )
    if not already_answered:
        if t in ("what is your name", "what's your name", "whats your name", "your name"):
            return _random.choice([
                "Mitra. Just someone you can talk to. What made you ask?",
                "You can call me Mitra. What's been on your mind?",
            ])
        if t in ("who are you", "what are you"):
            return _random.choice([
                "I'm just… someone you can talk to. What made you ask that?",
                "Honestly? I'm just here. What's on your mind?",
            ])

    # Repeated greeting (only if truly just a greeting word)
    if t in ("hey", "hi", "hello", "sup", "yo", "heya") and last_intent == "greeting":
        return _random.choice(_GREETING_FOLLOWUP_RESPONSES)

    return None


# ─── Personality-driven thinking messages ────────────────────────────────
THINKING_PHASES = {
    "default": [
        "Hmm…",
        "Okay…",
        "Yeah…",
        "Wait…",
    ],
    "mitra": [
        "Hmm…",
        "Oh…",
        "Okay, okay…",
        "Yeah…",
        "Wait—",
        "…",
    ],
    "mentor": [
        "Hmm.",
        "Interesting…",
        "Okay…",
        "Let me think…",
    ],
    "motivator": [
        "Okay—",
        "Alright…",
        "Yeah!",
        "Hmm, okay.",
    ],
    "coach": [
        "Okay.",
        "Right.",
        "Hmm.",
        "Got it—",
    ],
}

# Emotional words that get slower pacing
EMOTIONAL_WORDS = {
    "love", "sorry", "understand", "feel", "pain", "happy",
    "sad", "hurt", "scared", "brave", "strong", "hope",
    "cry", "smile", "hug", "breath", "calm", "peace",
    "afraid", "proud", "grateful", "trust", "safe", "alone",
    "together", "heart", "soul", "healing", "gentle", "okay",
}

# Sentence-end markers
SENTENCE_END = re.compile(r'[.!?…]+$')


# ─── Request / Response models ───────────────────────────────────────────
class StreamChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    personality: Optional[str] = None


# ─── Helpers ─────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event line."""
    payload = json.dumps({"type": event_type, **data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


def _split_sentences(text: str) -> List[str]:
    """Split text into natural sentence groups for grouped streaming."""
    # Split on sentence boundaries but keep the delimiter
    parts = re.split(r'(?<=[.!?…])\s+', text)
    return [p.strip() for p in parts if p.strip()]


async def _generate_stream(
    message: str,
    session_id: str,
    personality: str,
    user_id: Optional[int],
    db,
) -> AsyncGenerator[str, None]:
    """
    SOUL LOOP — Phase 5: Unified Soul System.

    One coherent being. Not modules.

      User speaks
        ↓ Emotion detected
        ↓ Memory recalled
        ↓ Growth context assembled
        ↓ Unified Mitra State built
        ↓ Care injection + human timing
        ↓ LLM response generated
        ↓ Automation opportunity detected
        ↓ Milestone witnessed
        ↓ UI rendered (emotion-aware)
    """

    # ── Step 1: Thinking indicator ───────────────────────────────────
    thinking_msgs = THINKING_PHASES.get(personality, THINKING_PHASES["default"])
    yield _sse_event("thinking", {
        "message": random.choice(thinking_msgs),
        "personality": personality,
    })

    # ── Step 2: Gather all context in parallel ───────────────────────
    emotion: Dict = {}
    intent = "general_support"
    memory_fragments: List[str] = []
    memory_used = False
    past_emotions: List[Dict] = []
    style_history: List[str] = []
    message_count = 0
    growth_arc = None
    milestones: List[Dict] = []
    days_together = 0
    user_name: Optional[str] = None

    # Memory retrieval (silent)
    try:
        if user_id and enhanced_chat_pipeline.long_term_memory:
            allowed = enhanced_chat_pipeline._get_allowed_memory_categories(user_id, db)
            raw = enhanced_chat_pipeline.long_term_memory.retrieve_memories(
                message, user_id, top_k=3, allowed_categories=allowed,
            )
            if raw:
                memory_fragments = [str(m) for m in raw if m]
                memory_used = bool(memory_fragments)
    except Exception:
        pass

    # Emotion + intent
    try:
        core = mitra_core(
            user_input=message,
            user_id=user_id,
            personality_used=personality,
            memory_context=memory_fragments,
        )
        emotion = core.get("emotion", {})
        intent = core.get("intent", "general_support")
    except Exception as e:
        logger.error(f"Core failed: {e}")

    primary_emotion = emotion.get("primary_emotion", "neutral")
    intensity = emotion.get("primary_intensity", "medium")

    # DB context: past emotions, message count, growth arc
    try:
        if user_id and db:
            from . import models
            records = db.query(models.EmotionRecord).filter(
                models.EmotionRecord.user_id == user_id
            ).order_by(models.EmotionRecord.timestamp.desc()).limit(15).all()
            past_emotions = [
                {"emotion": r.primary_emotion, "timestamp": r.timestamp.isoformat() if r.timestamp else None}
                for r in records
            ]
            message_count = db.query(models.ChatMessage).filter(
                models.ChatMessage.user_id == user_id
            ).count() or 0

            # Growth arc
            try:
                milestones = crud.get_user_milestones(db, user_id)
                chat_stats = crud.get_user_chat_stats(db, user_id)
                first_chat = chat_stats.get("first_chat_at")
                if first_chat:
                    if isinstance(first_chat, str):
                        first_chat = datetime.fromisoformat(first_chat)
                    days_together = max(0, (datetime.utcnow() - first_chat.replace(tzinfo=None)).days)
                growth_arc = build_relationship_arc(
                    emotion_history=past_emotions,
                    message_count=message_count,
                    days_since_first_chat=days_together,
                    milestones=milestones,
                )
            except Exception:
                pass

            # User name
            try:
                user_obj = crud.get_user(db, user_id) if hasattr(crud, 'get_user_by_id') else None
                if user_obj and hasattr(user_obj, 'username'):
                    user_name = user_obj.username
            except Exception:
                pass
    except Exception as e:
        logger.error(f"DB context failed: {e}")

    # Style detection
    current_style = detect_style_preference(message)
    if current_style:
        style_history.append(current_style)

    # ── Step 3: Build unified Mitra State ────────────────────────────
    mitra_st = build_mitra_state(
        user_input=message,
        current_emotion=primary_emotion,
        intensity=intensity,
        personality=personality,
        past_emotions=past_emotions,
        memory_fragments=memory_fragments,
        growth_arc=growth_arc,
        milestones=milestones,
        style_history=style_history,
        message_count=message_count,
        user_name=user_name,
    )

    care_mode = mitra_st["care_mode"]
    delay_profile = mitra_st["delay_profile"]

    # ── Step 4: Emit emotion event (UI adapts aura) ──────────────────
    if emotion:
        yield _sse_event("emotion", {
            "primary_emotion": primary_emotion,
            "primary_intensity": intensity,
            "confidence": emotion.get("confidence", 0.5),
            "care_mode": care_mode,
        })

    # ── Step 5: Soul layer (interjection + meaning moment) ───────────
    soul = build_soul_layer_instructions(
        current_emotion=primary_emotion,
        current_intensity=intensity,
        past_emotions=past_emotions,
        memory_fragments=memory_fragments,
        style_history=style_history,
        user_text=message,
        message_count=message_count,
    )
    interjection = soul.get("interjection")
    meaning_moment = soul.get("meaning_moment")

    if interjection or meaning_moment:
        yield _sse_event("soul", {
            "has_interjection": bool(interjection),
            "has_meaning_moment": bool(meaning_moment),
        })

    # ── Step 6: Human timing — BEFORE response ───────────────────────
    # The pause says "I'm actually thinking about what you said."
    await human_thinking_pause(primary_emotion, intensity)

    # Silence moment for heavy emotions
    silence_msg = get_silence_response(intensity)
    if silence_msg and primary_emotion in ("sad", "stressed", "anxious"):
        yield _sse_event("silence", {"message": silence_msg})
        await asyncio.sleep(delay_profile.get("thinking_delay", 1.4))

    # ── Step 7: Detect smart task opportunity ────────────────────────
    automation = detect_automation_opportunity(message, primary_emotion, intent)
    if automation:
        yield _sse_event("automation", {
            "offer": automation,
            "emotion": primary_emotion,
        })

    # ── Step 8: Generate response via unified Mitra state ────────────
    # Use session_id as key to isolate each conversation's state
    _session_key = session_id or str(user_id or "anon")
    _last_intent = _intent_cache.get(_session_key, "")
    _intent_cache[_session_key] = intent

    if _is_noise(message):
        full_response = random.choice(_NOISE_REPLIES)
    elif (quick := _get_quick_response(message, _last_intent, session_key=_session_key)):
        full_response = quick
    else:
        try:
            soul_instructions = mitra_st["system_prompt"]
            result = await enhanced_chat_pipeline.get_mitra_reply(
                user_input=message,
                user_id=user_id,
                db=db,
                personality=personality,
                session_id=session_id,
                soul_prompt=soul_instructions,
            )
            full_response = result.get("response", "")
            if not full_response or len(full_response.strip()) < 4:
                full_response = random.choice(_PRESENCE_FALLBACKS)
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            full_response = random.choice(_PRESENCE_FALLBACKS)

    # ── Presence filter: strip system language + prevent repeats ─────
    full_response = _sanitize_response(full_response, message, session_key=_session_key)

    # ── Step 9: Care injection ────────────────────────────────────────
    is_vulnerable = "vulnerable" in mitra_st.get("trajectory", "").lower()
    full_response, care_phrase = inject_care(
        full_response, primary_emotion, intensity,
        user_id=user_id, is_vulnerable=is_vulnerable,
    )

    # Organic interjection (soul engine)
    if interjection and not care_phrase:
        # Strip leading greeting from response to prevent "Hey… just so you know — Hey…"
        stripped = re.sub(r'^(hey|hi|hello)[^\w]*', '', full_response, flags=re.IGNORECASE).strip()
        body = stripped if stripped else full_response
        full_response = interjection + " " + body

    # Emotional reflection echo (brief acknowledgment before response)
    if not interjection and not care_phrase:
        echo = _reflection_prefix(primary_emotion, intensity)
        if echo:
            full_response = echo + full_response

    # Meaning moment
    if meaning_moment:
        full_response = full_response.rstrip() + "\n\n" + meaning_moment

    # Rare growth reflection
    full_response, did_reflect = maybe_add_reflection(
        full_response, days_together, len(milestones), primary_emotion
    )
    if did_reflect:
        yield _sse_event("soul", {"has_reflection": True})

    # ── Step 10: Stream with emotion-aware pacing ────────────────────
    if care_phrase:
        # Stream the care phrase alone first, then pause
        care_words = care_phrase.split()
        for i, w in enumerate(care_words):
            sep = "" if i == 0 else " "
            yield _sse_event("token", {"text": sep + w, "index": i, "is_care": True})
            await asyncio.sleep(0.08)
        yield _sse_event("token", {"text": "\n\n", "index": len(care_words)})
        await care_moment_pause()

    word_index = 0
    response_body = full_response
    if care_phrase:
        # Strip the care phrase from the body since we already streamed it
        response_body = full_response[len(care_phrase):].lstrip("\n")

    sentences = _split_sentences(response_body)
    base_delay = delay_profile.get("word_delay_base", 0.035)
    sentence_gap = delay_profile.get("sentence_gap", 0.18)

    for sent_i, sentence in enumerate(sentences):
        words = sentence.split()

        # Hesitation before emotional sentences
        if sent_i > 0 and sent_i <= 2:
            first_word = words[0].lower().rstrip(".,!?…") if words else ""
            is_emotional = (
                first_word in EMOTIONAL_WORDS or
                any(w.lower().rstrip(".,!?…") in EMOTIONAL_WORDS for w in words[:3])
            )
            if is_emotional and random.random() < 0.55:
                hesitation = get_hesitation_phrase(primary_emotion)
                if hesitation:
                    for hw in hesitation.split():
                        yield _sse_event("token", {"text": " " + hw, "index": word_index})
                        word_index += 1
                        await asyncio.sleep(0.11)
                    await asyncio.sleep(0.35)
        elif sent_i > 0:
            await asyncio.sleep(sentence_gap)

        for i, word in enumerate(words):
            sep = "" if word_index == 0 else " "
            yield _sse_event("token", {"text": sep + word, "index": word_index})
            word_index += 1

            clean = word.lower().rstrip(".,!?…;:'\"")
            delay = base_delay

            if clean in EMOTIONAL_WORDS:      delay = max(delay, 0.085)
            elif SENTENCE_END.search(word):   delay = max(delay, 0.16)
            elif word.endswith(","):          delay = max(delay, 0.07)
            elif word in ("…", "—"):          delay = max(delay, 0.22)
            elif i < 2 and sent_i == 0:       delay = max(delay, base_delay * 1.4)

            if intensity == "high":           delay *= 1.35
            elif intensity == "low":          delay *= 0.7

            await asyncio.sleep(delay)

    # ── Step 11: Emotion pattern detection ───────────────────────────
    pattern = None
    try:
        if user_id and db and past_emotions:
            pattern = detect_emotion_pattern(past_emotions)
            if pattern:
                yield _sse_event("pattern", pattern)
    except Exception:
        pass

    # ── Step 12: Done ────────────────────────────────────────────────
    yield _sse_event("done", {
        "full_response": full_response,
        "personality_used": personality,
        "session_id": session_id,
        "memory_used": memory_used,
        "memory_count": len(memory_fragments),
        "emotion": emotion,
        "intent": intent,
        "word_count": word_index,
        "pattern": pattern,
        "care_mode": care_mode,
        "automation": automation,
    })


# ─── Auth helper ─────────────────────────────────────────────────────────
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional), db=Depends(get_db)):
    if not token:
        return None
    try:
        user = security.get_current_user(token, db)
        return user
    except Exception:
        return None


# ─── Streaming chat route ────────────────────────────────────────────────
@router.post("/chat/stream")
async def chat_stream(
    request: StreamChatRequest,
    current_user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """
    Phase 3 Streaming SSE endpoint.
    Events: thinking → silence → emotion → token → pattern → done
    Memory is invisible — woven into AI prompt, never shown as UI banner.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    session_id = request.session_id or str(uuid.uuid4())
    personality = request.personality or "mitra"
    user_id = current_user.id if current_user else None

    return StreamingResponse(
        _generate_stream(
            message=request.message.strip(),
            session_id=session_id,
            personality=personality,
            user_id=user_id,
            db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── AI Initiative endpoint ─────────────────────────────────────────────
@router.get("/chat/initiative")
async def check_initiative(
    current_user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """
    Check if Mitra should proactively reach out.
    Frontend polls this periodically (every 5-10 min).
    Returns a message if conditions are met, else null.
    """
    if not current_user:
        return {"initiative": None}

    user_id = current_user.id

    # Get last chat timestamp
    try:
        messages = crud.get_recent_chat_history(db, user_id, limit=1)
        if not messages:
            return {"initiative": None}

        last_msg = messages[0]
        last_ts = last_msg.get("timestamp")
        if not last_ts:
            return {"initiative": None}

        if isinstance(last_ts, str):
            last_ts = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))

        hours_since = (datetime.utcnow() - last_ts.replace(tzinfo=None)).total_seconds() / 3600
    except Exception:
        hours_since = 0

    # Get last emotion
    last_emotion = "neutral"
    try:
        from . import models
        last_record = db.query(models.EmotionRecord).filter(
            models.EmotionRecord.user_id == user_id
        ).order_by(
            models.EmotionRecord.timestamp.desc()
        ).first()

        if last_record:
            last_emotion = last_record.primary_emotion or "neutral"
    except Exception:
        pass

    initiative = get_initiative_message(
        user_id=user_id,
        last_emotion=last_emotion,
        hours_since_last_chat=hours_since,
    )

    return {"initiative": initiative}


# ─── Emotion pattern endpoint ────────────────────────────────────────────
@router.get("/chat/patterns")
async def get_emotion_patterns(
    current_user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """
    Get detected emotional patterns for the user.
    Used by the UI to show insights like
    "I've noticed stress keeps coming up during exam weeks."
    """
    if not current_user:
        return {"pattern": None, "emotions": []}

    user_id = current_user.id

    try:
        from . import models
        records = db.query(models.EmotionRecord).filter(
            models.EmotionRecord.user_id == user_id
        ).order_by(
            models.EmotionRecord.timestamp.desc()
        ).limit(30).all()

        if not records:
            return {"pattern": None, "emotions": []}

        record_dicts = [
            {"emotion": r.primary_emotion, "timestamp": r.timestamp.isoformat() if r.timestamp else None}
            for r in records
        ]

        pattern = detect_emotion_pattern(record_dicts)

        return {
            "pattern": pattern,
            "emotion_count": len(records),
            "recent_emotions": [r.primary_emotion for r in records[:5]],
        }
    except Exception as e:
        logger.error(f"Pattern retrieval failed: {e}")
        return {"pattern": None, "emotions": []}


# ─── Slash commands (kept but simplified) ────────────────────────────────
class SlashCommandRequest(BaseModel):
    command: str
    session_id: Optional[str] = None


@router.post("/chat/command")
async def handle_slash_command(
    request: SlashCommandRequest,
    current_user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """Handle slash commands — /clear, /memory, /focus, /calm, /export."""
    cmd = request.command.strip().lower()
    user_id = current_user.id if current_user else None

    if cmd == "/clear":
        session_id = request.session_id
        if user_id and session_id:
            try:
                crud.delete_chat_session(db, user_id, session_id)
            except Exception:
                pass
        return {
            "command": "clear",
            "response": "Fresh start — I'm here whenever you're ready. ✨",
            "action": "clear_messages",
        }

    elif cmd == "/memory":
        if not user_id:
            return {"command": "memory", "response": "Sign in to access your memories. 🔒", "memories": []}

        memories = []
        try:
            if enhanced_chat_pipeline.long_term_memory:
                allowed = enhanced_chat_pipeline._get_allowed_memory_categories(user_id, db)
                raw = enhanced_chat_pipeline.long_term_memory.retrieve_memories(
                    "user preferences and routines", user_id, top_k=8, allowed_categories=allowed,
                )
                for m in raw:
                    text = str(m)
                    for prefix in ["[preference]", "[routine]", "[identity]", "[mental_health]"]:
                        text = text.replace(prefix, "").strip()
                    if text:
                        memories.append(text)
        except Exception:
            pass

        if memories:
            memory_text = "\n".join([f"• {m[:100]}" for m in memories[:5]])
            response = f"Here's what I remember:\n\n{memory_text}\n\nYour data stays local and encrypted. 🔒"
        else:
            response = "No memories yet. As we chat, I'll learn your preferences (with your permission). 💭"

        return {"command": "memory", "response": response, "memories": memories[:5], "action": "show_memory"}

    elif cmd == "/focus":
        return {
            "command": "focus",
            "response": "🎯 Focus mode. What's the one thing you need to accomplish?",
            "action": "set_personality",
            "personality": "coach",
        }

    elif cmd == "/calm":
        return {
            "command": "calm",
            "response": "🧘 Take a breath… I'm here. No rush.",
            "action": "set_personality",
            "personality": "mitra",
        }

    elif cmd == "/export":
        if not user_id:
            return {"command": "export", "response": "Sign in to export. 🔒", "action": "none"}
        return {
            "command": "export",
            "response": "Your data is encrypted and stored locally. Export ready. 📦",
            "action": "trigger_export",
        }

    else:
        return {
            "command": "unknown",
            "response": "Try: /clear, /memory, /focus, /calm, /export",
            "action": "none",
        }
