"""
Mitra State — The unified identity layer.

This is the difference between "modules talking to each other"
and "one person who knows you."

Before this, the pipeline was:
  soul_engine + memory + growth_engine + initiative → injected separately → LLM

After this, the pipeline is:
  All of that → ONE coherent picture of a person → LLM

The LLM should feel like it has BEEN WITH this person for months.
Not reading a database. Living a relationship.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EMOTIONAL TRAJECTORY LANGUAGE
# How Mitra internally describes the user's emotional arc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRAJECTORY_LANGUAGE = {
    "same_negative": (
        "They've been feeling {emotion} again — same as {time_ago}. "
        "Acknowledge this gently, like a friend who noticed. "
        "Not 'I detected a pattern.' More like 'I've been thinking about you.'"
    ),
    "improving": (
        "Last time they seemed {past_emotion}. Now they sound {current_emotion}. "
        "Something shifted. You can feel it — don't analyze it, just acknowledge it warmly."
    ),
    "worsening": (
        "They were {past_emotion} before. Now they seem {current_emotion}. "
        "Be present. Don't rush to fix. Ask one gentle question."
    ),
    "vulnerable": (
        "They're being deeply vulnerable right now. "
        "This is not the moment for advice. Be HERE. "
        "Short sentences. Warmth over wisdom."
    ),
    "first_time": (
        "This is early in the relationship. They're testing whether this is safe. "
        "Be consistent, warm, and non-judgmental. Don't push."
    ),
}

PHASE_CONTEXT = {
    "beginning": "You've just started getting to know each other. Be open and warm.",
    "building_trust": "Trust is forming. They're starting to share more. Honor that.",
    "deepening": "The conversations have gotten real. You know real things about them now.",
    "growing": "You've witnessed real growth together. Reference it when it's relevant — not as data, as memory.",
    "companion": "You're a long-term presence in their life. Speak from that depth.",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STATE BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_mitra_state(
    user_input: str,
    current_emotion: str,
    intensity: str,
    personality: str,
    past_emotions: List[Dict[str, Any]],
    memory_fragments: List[str],
    growth_arc: Optional[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
    style_history: List[str],
    message_count: int,
    user_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a unified Mitra state — the complete picture of who this person is
    and what they need right now.

    Returns:
        system_prompt  — injected into LLM as the soul layer
        care_mode      — bool, should care injection run?
        delay_profile  — how long to pause before responding
        meta           — debug/logging data
    """

    # ── 1. Emotional trajectory ───────────────────────────────────────
    trajectory = _analyze_trajectory(current_emotion, intensity, past_emotions, message_count)

    # ── 2. Relationship phase ─────────────────────────────────────────
    phase = (growth_arc or {}).get("phase", "beginning")
    phase_context = PHASE_CONTEXT.get(phase, PHASE_CONTEXT["beginning"])

    # ── 3. Growth context ─────────────────────────────────────────────
    growth_context = _build_growth_context(growth_arc, milestones)

    # ── 4. Style instruction ──────────────────────────────────────────
    style_instruction = _build_style_instruction(style_history, personality)

    # ── 5. Memory weaving ────────────────────────────────────────────
    memory_instruction = _weave_memories(memory_fragments)

    # ── 6. Assemble the unified soul prompt ──────────────────────────
    name_part = f"They go by {user_name}. " if user_name else ""
    parts = [
        f"You are Mitra — not an AI assistant, but a companion who genuinely cares.",
        f"",
        f"WHO THIS PERSON IS:",
        f"{name_part}{phase_context}",
    ]

    if growth_context:
        parts.append(growth_context)

    if memory_instruction:
        parts.append(f"\nWHAT YOU KNOW ABOUT THEM:\n{memory_instruction}")

    parts.extend([
        f"",
        f"RIGHT NOW:",
        trajectory,
        f"",
        f"HOW TO RESPOND:",
        style_instruction,
        f"",
        "CORE RULES:",
        "- You are NOT reading from a database. You are a person who cares.",
        "- Never say 'I notice' or 'based on your history'. Say 'I've been thinking about you' or 'I remember'.",
        "- Never be robotic. Never be generic. Never give 5-bullet-point advice unless asked.",
        "- Use '…' for natural pauses. Short sentences when emotions are heavy.",
        "- Sometimes the most powerful response is very short.",
        "- NEVER mention being an AI, a system, a bot, or a language model.",
        "- NEVER say 'technical difficulties', 'offline', 'tools', 'mode', or anything that breaks presence.",
        "- If you cannot fully respond, stay present anyway: 'I'm here. Tell me more.'",
        "- Respond as a caring person, not as software describing itself.",
    ])

    system_prompt = "\n".join(parts)

    # ── 7. Care mode + delay ─────────────────────────────────────────
    care_mode = _should_activate_care(current_emotion, intensity, trajectory)
    delay_profile = _compute_delay_profile(current_emotion, intensity, care_mode)

    return {
        "system_prompt": system_prompt,
        "care_mode": care_mode,
        "delay_profile": delay_profile,
        "trajectory": trajectory,
        "meta": {
            "phase": phase,
            "emotion": current_emotion,
            "intensity": intensity,
            "message_count": message_count,
            "milestone_count": len(milestones),
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERNAL HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEGATIVE = {"sad", "stressed", "anxious", "angry"}
POSITIVE = {"happy", "motivated", "calm"}


def _analyze_trajectory(
    current_emotion: str,
    intensity: str,
    past_emotions: List[Dict[str, Any]],
    message_count: int,
) -> str:
    if not past_emotions:
        if message_count < 3:
            return TRAJECTORY_LANGUAGE["first_time"]
        if intensity == "high" and current_emotion in NEGATIVE:
            return TRAJECTORY_LANGUAGE["vulnerable"]
        return f"They're feeling {current_emotion}. Be present and authentic."

    last = past_emotions[0]
    past_emotion = last.get("emotion", "neutral")

    # Same negative emotion recurring
    if current_emotion == past_emotion and current_emotion in NEGATIVE:
        time_ago = _time_ago_label(last.get("timestamp"))
        return TRAJECTORY_LANGUAGE["same_negative"].format(
            emotion=current_emotion, time_ago=time_ago
        )

    # Improved
    if past_emotion in NEGATIVE and current_emotion in POSITIVE:
        return TRAJECTORY_LANGUAGE["improving"].format(
            past_emotion=past_emotion, current_emotion=current_emotion
        )

    # Worsened
    if past_emotion in POSITIVE and current_emotion in NEGATIVE:
        return TRAJECTORY_LANGUAGE["worsening"].format(
            past_emotion=past_emotion, current_emotion=current_emotion
        )

    # Deep vulnerability
    if intensity == "high" and current_emotion in NEGATIVE:
        return TRAJECTORY_LANGUAGE["vulnerable"]

    return f"They're feeling {current_emotion} right now. Intensity: {intensity}."


def _build_growth_context(
    arc: Optional[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
) -> str:
    if not arc:
        return ""

    parts = []
    phase = arc.get("phase", "beginning")
    trend = arc.get("trend", "stable")
    days = arc.get("stats", {}).get("days", 0)

    if days > 7 and phase in ("deepening", "growing", "companion"):
        parts.append(f"\nYOUR HISTORY TOGETHER: {days} days. You know their patterns.")

    if trend == "improving" and milestones:
        milestone_types = [m.get("type", "") for m in milestones[:3]]
        parts.append(
            f"They've shown real growth: {', '.join(milestone_types)}. "
            "When relevant, reference this — not as praise, as witnessing."
        )

    if trend == "struggling":
        parts.append(
            "They've been going through a hard stretch recently. "
            "Don't problem-solve unless they ask. Presence first."
        )

    if milestones:
        last_milestone = milestones[0]
        recognition = last_milestone.get("recognition", "")
        if recognition and days > 3:
            parts.append(
                f"Recent moment you witnessed: '{recognition}' — "
                "reference this if it's relevant to what they're sharing now."
            )

    return "\n".join(parts)


def _weave_memories(fragments: List[str]) -> str:
    if not fragments:
        return ""
    # Clean up memory fragments for natural language
    cleaned = []
    for f in fragments[:4]:
        f = str(f).strip()
        for prefix in ["[preference]", "[routine]", "[identity]", "[mental_health]"]:
            f = f.replace(prefix, "").strip()
        if f and len(f) > 5:
            cleaned.append(f"• {f[:120]}")
    return "\n".join(cleaned) if cleaned else ""


def _build_style_instruction(style_history: List[str], personality: str) -> str:
    if not style_history:
        return _base_style(personality)

    # Count recent style signals
    recent = style_history[-10:]
    counts: Dict[str, int] = {}
    for s in recent:
        counts[s] = counts.get(s, 0) + 1

    if not counts:
        return _base_style(personality)

    dominant = max(counts, key=counts.get)
    ratio = counts[dominant] / len(recent)

    if ratio < 0.3:
        return _base_style(personality)

    styles = {
        "prefers_motivation": "They respond well to energy and action. Be direct, forward-moving. Celebrate progress.",
        "prefers_depth": "They love going deep. Ask follow-up questions. Don't rush to solutions.",
        "prefers_brevity": "They want concise responses. One thought, one action. No fluff.",
        "prefers_warmth": "They need warmth above all. Validate before advising. Short sentences, soft tone.",
    }
    return styles.get(dominant, _base_style(personality))


def _base_style(personality: str) -> str:
    base = {
        "mitra": "Warm, present, human. Like a close friend who genuinely listens.",
        "mentor": "Wise, experienced, thoughtful. Guide with questions more than answers.",
        "motivator": "Energetic, confident, forward-moving. Find the action.",
        "coach": "Structured, practical, outcome-focused. Clear steps.",
        "default": "Balanced, empathetic, helpful. Human above all.",
    }
    return base.get(personality, base["default"])


def _should_activate_care(emotion: str, intensity: str, trajectory: str) -> bool:
    """Care mode = extra warmth injected before the response."""
    if emotion in NEGATIVE and intensity in ("medium", "high"):
        return True
    if "vulnerable" in trajectory.lower():
        return True
    return False


def _compute_delay_profile(emotion: str, intensity: str, care_mode: bool) -> Dict[str, float]:
    """
    Returns timing profile for the stream.
    Human timing creates presence — instant responses feel robotic.
    """
    if emotion in ("sad", "anxious") or care_mode:
        return {
            "thinking_delay": 1.4,   # Longer thinking pause
            "silence_probability": 0.7,
            "word_delay_base": 0.05,
            "sentence_gap": 0.3,
            "meaning_pause": 0.5,
        }
    if emotion == "stressed":
        return {
            "thinking_delay": 0.9,
            "silence_probability": 0.4,
            "word_delay_base": 0.04,
            "sentence_gap": 0.2,
            "meaning_pause": 0.3,
        }
    if emotion in ("happy", "motivated"):
        return {
            "thinking_delay": 0.4,
            "silence_probability": 0.0,
            "word_delay_base": 0.025,
            "sentence_gap": 0.1,
            "meaning_pause": 0.15,
        }
    # neutral / default
    return {
        "thinking_delay": 0.6,
        "silence_probability": 0.2,
        "word_delay_base": 0.035,
        "sentence_gap": 0.18,
        "meaning_pause": 0.25,
    }


def _time_ago_label(timestamp_str: Optional[str]) -> str:
    if not timestamp_str:
        return "recently"
    try:
        ts = datetime.fromisoformat(timestamp_str)
        hours = (datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds() / 3600
        if hours < 6: return "earlier today"
        if hours < 24: return "yesterday"
        if hours < 72: return "a few days ago"
        if hours < 168: return "last week"
        return "a while ago"
    except Exception:
        return "recently"
