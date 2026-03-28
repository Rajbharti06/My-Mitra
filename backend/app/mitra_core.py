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
    hidden_signal = emo.get("hidden_signal")

    # Use .value to get plain strings so downstream comparisons work reliably
    # (str(EmotionCategory.X) returns "EmotionCategory.X" in Python 3.12+).
    # Guard against None in case the detection result is ever incomplete.
    primary_str = primary.value if primary is not None and hasattr(primary, "value") else (str(primary) if primary else "neutral")
    intensity_str = intensity.value if intensity is not None and hasattr(intensity, "value") else (str(intensity) if intensity else "medium")

    return {
        "primary_emotion": primary_str,
        "primary_intensity": intensity_str,
        "confidence": float(emo.get("confidence", 0.5)),
        "hidden_signal": hidden_signal,
    }


def choose_mode(intent: str, emotion: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Returns:
      mode_label: "fast" | "deliberate"
      fast_mode: bool
    """
    intensity = emotion.get("primary_intensity", "medium")
    emo = emotion.get("primary_emotion")

    if intent in ["file_list_request", "file_read_request", "file_delete_request", "chat_retention_request"]:
        # Usually quick + concrete.
        return ("fast", True)

    # Emotional intensity -> slow down for grounding.
    if intensity == "high" or emo in ["anxious", "stressed", "sad", "numb", "lonely"]:
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
    if emo == "numb":
        return (
            "Behavior controller: be gentle and activating. "
            "Acknowledge the emptiness without judgment. "
            "Offer one tiny, low-effort action to re-engage — no pressure, no rush. "
            "Use warm, grounding language that creates presence without forcing energy."
        )
    if emo == "lonely":
        return (
            "Behavior controller: be warm and connecting. "
            "Make the user feel genuinely seen and not alone in this moment. "
            "Avoid generic platitudes. Offer real presence + one small social or self-connection action."
        )
    return (
        "Behavior controller: neutral, supportive tone. "
        "Offer options and ask one helpful question at the end."
    )


def _fuse_personalities(emotion: Dict[str, Any], intent: str) -> List[str]:
    """
    Determine which personalities to blend based on emotion and intent.
    Returns a list of 1–2 personality names (primary first).

    Fusion rules (spec: "FUSION, NOT SWITCHING"):
      sad / numb / lonely          → mitra + mentor  (empathy + wisdom)
      goal-related intents         → coach + mentor   (discipline + guidance)
      low-energy (stressed/burnout)→ motivator + mitra (activation + warmth)
      anxious                      → mitra + coach    (grounding + structure)
      motivated                    → motivator + coach (energy + direction)
      default                      → mitra alone
    """
    emo = emotion.get("primary_emotion", "neutral")
    hidden = emotion.get("hidden_signal")
    goal_intents = {"study_request", "focus_request", "habit_request", "journal_request"}

    if emo in ("sad", "numb", "lonely"):
        return ["mitra", "mentor"]
    if intent in goal_intents:
        return ["coach", "mentor"]
    if emo in ("stressed",) or hidden == "burnout":
        return ["motivator", "mitra"]
    if emo == "anxious":
        return ["mitra", "coach"]
    if emo == "motivated":
        return ["motivator", "coach"]
    return ["mitra"]


def derive_identity_profile(
    user_input: str,
    intent: str,
    emotion: Dict[str, Any],
    memory_context: List[str],
    persisted: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the per-request identity snapshot used to shape the LLM response.

    Heuristics run first; then *stable* fields from `persisted` (the SQL
    UserIdentityProfile) override the heuristic where a value exists.  This
    means the profile "gets smarter" over time without losing session-level
    awareness.
    """
    text = (user_input or "").lower()

    # --- Heuristic traits (session-level) ---
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

    if intent in ("study_request", "focus_request"):
        current_phase = "exam_preparation"
    elif intent in ("journal_request", "emotional_support"):
        current_phase = "self_reflection"
    elif intent == "habit_request":
        current_phase = "habit_formation"
    else:
        current_phase = "general_growth"

    decision_style = (
        "hesitant"
        if any(k in text for k in ["should i", "what do i do", "not sure", "i can't decide", "maybe", "doubt"])
        else "clarity_seeking"
    )

    # --- Merge persisted stable fields (override heuristics where known) ---
    p = persisted or {}
    stable_user_type = p.get("user_type")
    stable_decision_pattern = p.get("decision_pattern") or decision_style
    stable_energy_cycle = p.get("energy_cycle") or energy_pattern
    stable_core_goal = p.get("core_goal") or current_phase
    persisted_traits: List[str] = p.get("core_traits") or []

    # Merge trait lists (persisted first for weight, session heuristics appended)
    merged_traits = list(dict.fromkeys(persisted_traits + core_traits))[:6]

    return {
        # Spec-aligned stable fields
        "user_type": stable_user_type,
        "decision_pattern": stable_decision_pattern,
        "energy_cycle": stable_energy_cycle,
        "core_goal": stable_core_goal,
        "core_traits": merged_traits,
        # Session-level fields (for contextual shaping)
        "current_phase": current_phase,
        "energy_pattern": energy_pattern,
        "decision_style": decision_style,
        "observation_count": p.get("observation_count", 0),
    }


def build_identity_instructions(identity: Dict[str, Any]) -> str:
    parts = ["Identity layer:"]

    user_type = identity.get("user_type")
    if user_type:
        parts.append(f"This user is a '{user_type}'.")

    decision_pattern = identity.get("decision_pattern")
    if decision_pattern:
        parts.append(f"Decision pattern: {decision_pattern}.")

    energy_cycle = identity.get("energy_cycle")
    if energy_cycle:
        parts.append(f"Energy cycle: {energy_cycle}.")

    core_goal = identity.get("core_goal")
    if core_goal:
        parts.append(f"Core goal: {core_goal}.")

    traits = identity.get("core_traits")
    if traits:
        parts.append(f"Core traits: {', '.join(str(t) for t in traits)}.")

    parts.append(
        f"Current session phase: {identity.get('current_phase')}; "
        f"decision style: {identity.get('decision_style')}. "
        "Adjust tone, depth, and how assertively you guide based on this profile."
    )

    return " ".join(parts)


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
    persisted_identity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Core brain orchestrator. It returns prompt-shaping metadata and action suggestions.
    LLM call still happens in the caller (EnhancedChatPipeline) so we can keep caching/memory storage central.

    `persisted_identity` is the stable UserIdentityProfile loaded from the DB.
    It is merged with session-level heuristics inside derive_identity_profile().
    """
    intent = detect_intent(user_input)
    emotion = detect_emotion_behavior(user_input)
    mode_label, fast_mode = choose_mode(intent, emotion)

    identity_profile = derive_identity_profile(
        user_input, intent, emotion, memory_context, persisted=persisted_identity
    )

    # Personality fusion: blend roles based on emotion + intent (FUSION, NOT SWITCHING).
    fused_personalities = _fuse_personalities(emotion, intent)
    primary_personality = fused_personalities[0]
    secondary_personality = fused_personalities[1] if len(fused_personalities) > 1 else None

    if secondary_personality:
        fusion_instruction = (
            f"Personality fusion: blend {primary_personality.upper()} (primary) "
            f"with {secondary_personality.upper()} (secondary). "
            f"Lead with {primary_personality} qualities, enrich with {secondary_personality} wisdom. "
            f"Intent is '{intent}'. Provide guidance that feels both human and actionable."
        )
    else:
        fusion_instruction = (
            f"Personality fusion: respond as {primary_personality.upper()} — "
            "warm, empathetic, and grounding."
        )

    hidden_signal = emotion.get("hidden_signal")

    instructions = [
        build_identity_instructions(identity_profile),
        behavior_controller(emotion),
        fusion_instruction,
        "Safety: never claim you executed an action. If you propose any action, return it as a suggestion requiring user approval.",
    ]
    if hidden_signal:
        instructions.insert(3, f"Hidden signal detected: '{hidden_signal}'. Address it gently without naming it directly.")

    extra_system_instructions = "\n".join(instructions)

    action_suggestions = decide_action_suggestions(intent, user_input)

    return {
        "intent": intent,
        "emotion": emotion,
        "mode_label": mode_label,
        "fast_mode": fast_mode,
        "identity_profile": identity_profile,
        "extra_system_instructions": extra_system_instructions,
        "action_suggestions": action_suggestions,
        # fused_personalities drives prompt blending in the LLM layer.
        "personality_used": primary_personality,
        "fused_personalities": fused_personalities,
    }
