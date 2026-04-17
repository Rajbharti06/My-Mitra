"""
Smart Tasks — Gentle automation that feels like companionship.

The difference:

❌ Tool:     "Would you like me to set a 25-minute timer?"
✅ Companion: "Let's try 25 minutes together. I'll stay here."

This module detects situations where Mitra can help
without being asked — and offers them as collaboration,
not commands.

Categories:
  FOCUS    — can't focus, need to work, procrastinating
  STUDY    — exam, test, need to study, revision
  HABIT    — should exercise, want to read, trying to sleep better
  PLAN     — overwhelmed, too much, don't know where to start
  BREATHE  — panic, heart racing, need to calm down
"""

import re
from typing import Optional, List, Dict, Any


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECTION PATTERNS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK_PATTERNS = [
    {
        "id": "focus_timer",
        "category": "focus",
        "patterns": [
            r"\bcan'?t focus\b", r"\bcan'?t concentrate\b", r"\bkeep getting distracted\b",
            r"\bneed to (work|study|finish|do)\b", r"\bprocrastinat\b",
            r"\bwasted (the |my )?(whole |entire )?(day|morning|evening)\b",
            r"\bfocus (mode|timer|session)\b", r"\bpomodoro\b",
        ],
        "offer": {
            "text": "Let's try 25 minutes together. Just you and the work — I'll be right here.",
            "action": "start_focus_timer",
            "params": {"duration_minutes": 25, "label": "Focus session"},
            "button_label": "Start 25-min focus",
        },
    },
    {
        "id": "study_plan",
        "category": "study",
        "patterns": [
            r"\b(exam|test|quiz|assessment) (is |in )?(tomorrow|today|tonight|this week)\b",
            r"\bneed to (revise|study|prepare|review)\b",
            r"\bstudying (for|tonight|today)\b",
            r"\bhave (an |a )?exam\b", r"\bbig (test|exam)\b",
        ],
        "offer": {
            "text": "Let's make a quick study plan together. What subject, and how much time do you have?",
            "action": "create_study_plan",
            "params": {"type": "study_plan"},
            "button_label": "Build study plan",
        },
    },
    {
        "id": "breathing_exercise",
        "category": "breathe",
        "patterns": [
            r"\bpanic\b", r"\bheart (is )?racing\b", r"\bcan'?t breathe\b",
            r"\boverwhel?med\b", r"\bspiraling\b", r"\banxiety (is |attack)\b",
            r"\bneed to calm (down|myself)\b", r"\bbreaking (down|apart)\b",
        ],
        "offer": {
            "text": "Let's breathe together for just one minute. 4 counts in, 4 counts hold, 4 counts out.",
            "action": "start_breathing",
            "params": {"pattern": "box_4", "duration_seconds": 60},
            "button_label": "Start breathing",
        },
    },
    {
        "id": "habit_create",
        "category": "habit",
        "patterns": [
            r"\b(want to|should|trying to) (start |build )?(exercising|working out|running|meditating|reading|sleeping earlier|waking up early)\b",
            r"\b(want to|need to) (build|create|start) a (habit|routine)\b",
            r"\bif i (just|could) (do|stick to|be consistent with)\b",
        ],
        "offer": {
            "text": "Want me to add that as a habit you're building? I can track it with you every day.",
            "action": "create_habit",
            "params": {"type": "habit"},
            "button_label": "Create habit",
        },
    },
    {
        "id": "priority_list",
        "category": "plan",
        "patterns": [
            r"\btoo much (to do|going on|on my plate)\b",
            r"\bdon'?t know where to start\b",
            r"\bfeeling overwhelmed (with|by)? (tasks|work|everything|school)\b",
            r"\bso (many|much) things\b",
            r"\b(buried|drowning|swamped) (in|with)\b",
        ],
        "offer": {
            "text": "Let's figure out what actually matters right now. Tell me everything on your mind — we'll sort it together.",
            "action": "create_priority_list",
            "params": {"type": "priority_list"},
            "button_label": "Sort priorities",
        },
    },
    {
        "id": "journal_prompt",
        "category": "reflect",
        "patterns": [
            r"\bneed to (think|process|figure) (this |it )?out\b",
            r"\bdon'?t know how i feel\b",
            r"\bconfused about\b", r"\bspinning in my head\b",
            r"\bso much in my head\b", r"\bthinking (too much|constantly|nonstop)\b",
        ],
        "offer": {
            "text": "Sometimes writing it out helps. Want to open a journal entry right now?",
            "action": "open_journal",
            "params": {"type": "journal"},
            "button_label": "Open journal",
        },
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DETECTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_automation_opportunity(
    user_text: str,
    current_emotion: str = "neutral",
    intent: str = "general_support",
) -> Optional[Dict[str, Any]]:
    """
    Detect if the user's message opens an opportunity for gentle automation.

    Returns the first matching task offer, or None.
    Priority: breathe > focus > study > habit > plan > reflect
    """
    text_lower = user_text.lower()

    priority_order = ["breathing_exercise", "focus_timer", "study_plan", "habit_create", "priority_list", "journal_prompt"]

    matches = {}
    for task in TASK_PATTERNS:
        for pattern in task["patterns"]:
            if re.search(pattern, text_lower):
                matches[task["id"]] = task
                break

    # Return in priority order
    for task_id in priority_order:
        if task_id in matches:
            return matches[task_id]["offer"]

    return None


def detect_multiple_opportunities(
    user_text: str,
) -> List[Dict[str, Any]]:
    """Return all detected automation opportunities (max 2)."""
    text_lower = user_text.lower()
    found = []
    seen_categories = set()

    for task in TASK_PATTERNS:
        for pattern in task["patterns"]:
            if re.search(pattern, text_lower):
                cat = task["category"]
                if cat not in seen_categories:
                    seen_categories.add(cat)
                    found.append(task["offer"])
                if len(found) >= 2:
                    return found
                break

    return found


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STUDY PLAN GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_study_plan(subject: str, hours_available: float) -> Dict[str, Any]:
    """Generate a simple study plan when time is tight."""
    slots = []
    remaining = hours_available

    if remaining >= 3:
        slots.append({"label": "Review key concepts", "duration": 45, "type": "review"})
        slots.append({"label": "Practice problems", "duration": 60, "type": "practice"})
        slots.append({"label": "Weak areas focus", "duration": 45, "type": "focus"})
        slots.append({"label": "Quick revision + rest", "duration": 30, "type": "rest"})
    elif remaining >= 1.5:
        slots.append({"label": "High-priority topics only", "duration": 45, "type": "review"})
        slots.append({"label": "Practice the hardest things", "duration": 30, "type": "practice"})
        slots.append({"label": "Quick review + sleep", "duration": 15, "type": "rest"})
    else:
        slots.append({"label": "The 3 most likely exam topics", "duration": 30, "type": "review"})
        slots.append({"label": "Rest — fatigue kills recall", "duration": 20, "type": "rest"})

    return {
        "subject": subject,
        "total_hours": hours_available,
        "slots": slots,
        "reminder": "You know more than you think. Trust the work you've already done.",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PRIORITY SORTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sort_priorities(tasks_text: str) -> Dict[str, Any]:
    """
    Simple priority sorting from a text list.
    Returns a structured priority list.
    """
    lines = [l.strip() for l in tasks_text.split("\n") if l.strip()]
    lines = [l.lstrip("•-*123456789. ") for l in lines]

    urgent_keywords = ["today", "tomorrow", "deadline", "due", "urgent", "asap", "now", "tonight"]
    important_keywords = ["exam", "work", "submit", "project", "meeting", "appointment"]

    urgent = []
    important = []
    rest = []

    for task in lines:
        tl = task.lower()
        if any(k in tl for k in urgent_keywords):
            urgent.append(task)
        elif any(k in tl for k in important_keywords):
            important.append(task)
        else:
            rest.append(task)

    return {
        "urgent": urgent,
        "important": important,
        "can_wait": rest,
        "focus_on": (urgent + important)[:1],
    }
