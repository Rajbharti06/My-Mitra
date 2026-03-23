"""
Mitra Core Brain (lightweight orchestration).

Single "brainstem" flow:
  Understand (intent + emotion)
  Remember (memory context + identity derivation)
  Decide (mode + action suggestions)
  Think (prompt shaping for the LLM)
  Act (return suggestions; execution happens only after explicit approval)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.emotion_engine import emotion_engine


def detect_intent(user_input: str) -> str:
    text = (user_input or "").lower()

    # System actions (file operations / retention)
    if any(k in text for k in ["list files", "list file", "show files", "ls "]):
        return "file_list_request"
    if any(k in text for k in ["read file", "open file", "show me", "read ", "cat "]):
        return "file_read_request"
    if any(k in text for k in ["delete file", "remove file", "delete ", "rm "]):
        return "file_delete_request"
    if any(k in text for k in ["retention", "keep chats", "history retention", "days"]):
        return "chat_retention_request"

    # Life / planning
    if any(k in text for k in ["study", "exam", "assignment", "homework", "revision", "syllabus"]):
        return "study_request"
    if any(k in text for k in ["focus", "pomodoro", "work session", "study session", "timer"]):
        return "focus_request"
    if any(k in text for k in ["journal", "write down", "entry"]):
        return "journal_request"
    if any(k in text for k in ["habit", "daily", "weekly", "track habit"]):
        return "habit_request"

    if any(k in text for k in ["i feel", "i'm feeling", "i am feeling", "i feel like", "anxious", "stressed", "sad", "angry"]):
        return "emotional_support"

    return "general_support"


def detect_emotion_behavior(user_input: str) -> Dict[str, Any]:
    # Lightweight emotion detection: rule-based only.
    emo = emotion_engine._rule_based_detection(user_input)
    primary = emo.get("primary_emotion")
    intensity = emo.get("primary_intensity")

    return {
        "primary_emotion": str(primary),
        "primary_intensity": str(intensity),
        "confidence": float(emo.get("confidence", 0.5)),
    }


def choose_mode(intent: str, emotion: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Returns:
      mode_label: "fast" | "deliberate"
      fast_mode: bool
    """
    intensity = emotion.get("primary_intensity", "medium")

    if intent in ["file_list_request", "file_read_request", "file_delete_request", "chat_retention_request"]:
        # Usually quick + concrete.
        return ("fast", True)

    # Emotional intensity -> slow down for grounding.
    if intensity == "high" or emotion.get("primary_emotion") in ["anxious", "stressed", "sad"]:
        return ("deliberate", False)

    return ("fast" if intent in ["focus_request", "study_request", "habit_request"] else "deliberate",
            intent in ["focus_request", "study_request", "habit_request"])


def behavior_controller(emotion: Dict[str, Any]) -> str:
    """
    Convert emotion -> behavior controller (tone + structure),
    keeping it short and deterministic for reliability.
    """
    emo = emotion.get("primary_emotion")
    intensity = emotion.get("primary_intensity")

    if emo == "anxious":
        return (
            "Behavior controller: tone should be slow, grounding, and reassuring. "
            "Use a step-by-step structure (1–3 steps). Keep response short. "
            "Do a micro-breath cue before advice."
        )
    if emo == "stressed":
        return (
            "Behavior controller: validate first, then reduce cognitive load. "
            "Provide 1–2 actionable steps, and one 'what can wait' line. "
            "Keep it practical and calming."
        )
    if emo == "sad":
        return (
            "Behavior controller: be gentle and emotionally present. "
            "Use reflective language, avoid rushing to solutions. "
            "Offer small comfort + one tiny next action."
        )
    if emo == "angry":
        return (
            "Behavior controller: de-escalate with empathy. "
            "Acknowledge impact, then offer options (2 choices max) and a safe next step."
        )
    if emo == "confused":
        return (
            "Behavior controller: simplify. Break the problem into a 'what we know' and 'next question'. "
            "Ask one focused clarifying question if needed."
        )
    if emo == "motivated":
        return (
            "Behavior controller: match the energy. Provide a clear plan with a quick win first. "
            "Use confident language."
        )
    return (
        "Behavior controller: neutral, supportive tone. "
        "Offer options and ask one helpful question at the end."
    )


def derive_identity_profile(
    user_input: str,
    intent: str,
    emotion: Dict[str, Any],
    memory_context: List[str],
) -> Dict[str, Any]:
    """
    Lightweight identity extraction (heuristic).
    Stored as a structured profile via adaptive memory later.
    """
    text = (user_input or "").lower()

    core_traits: List[str] = []
    joined = " ".join(memory_context[:8]).lower() if memory_context else ""

    if any(k in joined for k in ["overthink", "doubt", "uncertain", "not sure", "hesitant"]):
        core_traits.append("overthinker")
    if any(k in joined for k in ["routine", "habit", "schedule", "plan", "disciplined"]):
        core_traits.append("disciplined")
    if any(k in text for k in ["i'm trying", "i want to", "i need to"]):
        core_traits.append("growth_oriented")

    if not core_traits:
        core_traits = ["seeking_clarity"]

    hour = datetime.now().hour
    if hour < 6:
        energy_pattern = "late_night_low"
    elif hour < 12:
        energy_pattern = "morning"
    elif hour < 17:
        energy_pattern = "afternoon_focus"
    elif hour < 22:
        energy_pattern = "evening"
    else:
        energy_pattern = "late_night"

    if emotion.get("primary_emotion") in ["stressed", "anxious", "sad"] and hour >= 17:
        energy_pattern = "low_evening"

    if intent == "study_request" or intent == "focus_request":
        current_phase = "exam_preparation"
    elif intent in ["journal_request", "emotional_support"]:
        current_phase = "self_reflection"
    elif intent in ["habit_request"]:
        current_phase = "habit_formation"
    else:
        current_phase = "general_growth"

    decision_style = "hesitant" if any(k in text for k in ["should i", "what do i do", "not sure", "i can't decide", "maybe", "doubt"]) else "clarity_seeking"

    return {
        "core_traits": core_traits[:4],
        "current_phase": current_phase,
        "energy_pattern": energy_pattern,
        "decision_style": decision_style,
    }


def build_identity_instructions(identity: Dict[str, Any]) -> str:
    return (
        "Identity layer (behavioral, inferred): "
        f"core_traits={identity.get('core_traits')}; "
        f"current_phase={identity.get('current_phase')}; "
        f"energy_pattern={identity.get('energy_pattern')}; "
        f"decision_style={identity.get('decision_style')}. "
        "Use this to steer tone, structure, and how strongly you push for action."
    )


def _extract_potential_path_tokens(text: str, max_tokens: int = 4) -> List[str]:
    tokens = re.findall(r"[\w\-\.\~/\\\\]+", text)
    # Keep tokens that look like paths/files (contain / or \ or . and have extension-like dot)
    out: List[str] = []
    for t in tokens:
        if "http" in t:
            continue
        if len(out) >= max_tokens:
            break
        if ("/" in t or "\\" in t) or (("." in t and not t.isdigit())):
            out.append(t)
    return out


def decide_action_suggestions(intent: str, user_input: str) -> List[Dict[str, Any]]:
    """
    Return suggestions only. Actual execution happens via preview/commit.
    """
    text = (user_input or "").lower()
    suggestions: List[Dict[str, Any]] = []

    # Retention suggestion
    if intent == "chat_retention_request":
        m = re.search(r"(\d{1,3})\s*days", text)
        if m:
            days = int(m.group(1))
            suggestions.append({
                "kind": "system",
                "action_type": "set_chat_history_retention_days",
                "summary": f"Set chat history retention to {days} days",
                "params": {"days": days},
            })
        return suggestions

    # File suggestions: conservative parsing to avoid nonsense actions.
    path_tokens = _extract_potential_path_tokens(user_input, max_tokens=3)
    rel_path = None
    for tok in path_tokens:
        if tok and ".." not in tok and len(tok) <= 200:
            rel_path = tok.replace("\\", "/").lstrip("/")
            break

    if intent == "file_read_request" and rel_path:
        suggestions.append({
            "kind": "system",
            "action_type": "file_read_text",
            "summary": f"Read file `{rel_path}` (truncated preview)",
            "params": {"relative_path": rel_path, "max_bytes": 50000},
        })
    elif intent == "file_delete_request" and rel_path:
        suggestions.append({
            "kind": "system",
            "action_type": "file_delete",
            "summary": f"Delete file `{rel_path}`",
            "params": {"relative_path": rel_path},
        })
    elif intent == "file_list_request":
        # Try to extract directory token after "in"
        m = re.search(r"\bin\s+([^\s]+)", text)
        rel_dir = m.group(1).replace("\\", "/").lstrip("/") if m else ""
        if rel_dir and ".." not in rel_dir:
            rel_dir = rel_dir[:200]
        suggestions.append({
            "kind": "system",
            "action_type": "file_list",
            "summary": f"List files in `{rel_dir}`",
            "params": {"relative_dir": rel_dir},
        })

    return suggestions


def mitra_core(
    user_input: str,
    user_id: Optional[int],
    personality_used: str,
    memory_context: List[str],
) -> Dict[str, Any]:
    """
    Core brain orchestrator. It returns prompt-shaping metadata and action suggestions.
    LLM call still happens in the caller (EnhancedChatPipeline) so we can keep caching/memory storage central.
    """
    intent = detect_intent(user_input)
    emotion = detect_emotion_behavior(user_input)
    mode_label, fast_mode = choose_mode(intent, emotion)

    identity_profile = derive_identity_profile(user_input, intent, emotion, memory_context)

    # Fuse emotion -> behavior -> identity into deterministic extra instructions.
    fusion_instruction = (
        "Personality fusion: keep Mitra-style empathy while also matching the intent: "
        f"intent={intent}. Provide actionable guidance with calm confidence."
    )

    extra_system_instructions = "\n".join([
        build_identity_instructions(identity_profile),
        behavior_controller(emotion),
        fusion_instruction,
        "Safety: never claim you executed an action. If you propose any action, return it as a suggestion requiring user approval.",
    ])

    action_suggestions = decide_action_suggestions(intent, user_input)

    return {
        "intent": intent,
        "emotion": emotion,
        "mode_label": mode_label,
        "fast_mode": fast_mode,
        "identity_profile": identity_profile,
        "extra_system_instructions": extra_system_instructions,
        "action_suggestions": action_suggestions,
        # personality fusion currently uses prompt shaping; runtime personality remains primary.
        "personality_used": personality_used,
    }

