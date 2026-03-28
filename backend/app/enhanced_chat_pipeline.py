#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced chat pipeline for My Mitra with Ollama integration.
Supports multiple AI personalities and long-term memory.
"""

import os
import uuid
import logging
from typing import Optional, List, Dict, Any
import re
import json
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from llm.ollama_model import OllamaMyMitraModel, PersonalityType
from vector_memory import LongTermMemory
from . import crud
from .mitra_core import mitra_core

logger = logging.getLogger(__name__)

# Trait values produced by heuristics as placeholders — not meaningful enough to persist.
# They are session-only anchors to avoid polluting stable identity with vague defaults.
# Example: "seeking_clarity" is a catch-all fallback when we lack signal; it should never fossilize in the profile.
_EPHEMERAL_TRAIT_PLACEHOLDERS: frozenset = frozenset(["seeking_clarity"])


class EnhancedChatPipeline:
    """Enhanced chat pipeline with personality, memory, and caching."""

    def __init__(self):
        self.model = OllamaMyMitraModel()
        try:
            self.long_term_memory = LongTermMemory()
        except Exception:
            self.long_term_memory = None

    async def get_mitra_reply(
        self,
        user_input: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        personality: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Mitra AI reply; store and use session-specific context when available."""
        # Determine personality
        personality_used = self._determine_personality(user_id, personality, db)
        personality_type = self._string_to_personality_enum(personality_used)

        # Build context (recent conversation for this session only)
        context_messages: List[Dict[str, str]] = []
        if user_id and db:
            context_messages = self._get_conversation_context(user_id, db, session_id=session_id)

        # Load persisted identity profile (may be None for new users)
        persisted_identity: Dict[str, Any] = {}
        if user_id and db:
            try:
                raw_profile = crud.get_identity_profile(db, user_id)
                persisted_identity = crud.identity_profile_to_dict(raw_profile)
            except Exception as e:
                logger.warning(f"Could not load identity profile: {e}")

        # Defaults (needed for caching path as well).
        depth_level = 1
        use_fast_mode = False
        emotion: Dict[str, Any] = {}
        intent: str = "general_support"
        identity_profile: Dict[str, Any] = {}
        action_suggestions: List[Dict[str, Any]] = []
        extra_system_instructions: Optional[str] = None
        fused_personalities: Optional[List[str]] = None

        # Check cached response path for general FAQs
        normalized_q = self._normalize_question(user_input)
        cached = None
        if db:
            try:
                cached = crud.get_cached_response(db, normalized_q, personality_used)
            except Exception:
                cached = None

        if cached:
            ai_text = cached
            memory_used = False
            # Still compute lightweight shaping outputs so UI remains consistent.
            depth_level = self._estimate_conversation_depth(user_input, context_messages)
            use_fast_mode = depth_level <= 2 and len(user_input) < 160
        else:
            # Ensure model personality matches selection
            try:
                self.model.set_personality(personality_type)
            except Exception:
                pass

            # Build long-term memory context if available
            long_term_context: List[str] = []
            try:
                if user_id and self.long_term_memory:
                    long_term_context = self._get_memory_context(user_input, user_id, db)
            except Exception:
                long_term_context = []

            # Mitra Core Brain: intent + emotion -> behavior + identity -> action suggestions.
            core = mitra_core(
                user_input=user_input,
                user_id=user_id,
                personality_used=personality_used,
                memory_context=long_term_context,
                persisted_identity=persisted_identity,
            )

            # Estimate conversation depth and choose fast mode accordingly (keeps latency adaptive).
            depth_level = self._estimate_conversation_depth(user_input, context_messages)
            use_fast_mode = bool(core.get("fast_mode", depth_level <= 2 and len(user_input) < 160))
            emotion = core.get("emotion", {})
            intent = core.get("intent", "general_support")
            identity_profile = core.get("identity_profile", {})
            action_suggestions = core.get("action_suggestions", [])
            extra_system_instructions = core.get("extra_system_instructions")
            fused_personalities = core.get("fused_personalities")

            # Generate response via model with conversation and memory context
            ai_text = await self.model.generate_response(
                user_input,
                conversation_history=context_messages,
                long_term_memory_context=long_term_context,
                fast_mode=use_fast_mode,
                extra_system_instructions=extra_system_instructions,
                fused_personalities=fused_personalities,
            )
            memory_used = bool(context_messages or long_term_context)

        # Persist conversation if authenticated and capture timestamp
        created_at_iso: Optional[str] = None
        try:
            if user_id and db:
                stored = self._store_conversation(db, user_id, user_input, ai_text, personality_used, session_id)
                try:
                    created_at_iso = stored.created_at.isoformat() if getattr(stored, 'created_at', None) else None
                except Exception:
                    created_at_iso = None

                # Cache only non-personal replies (no memory context used).
                if not memory_used and db:
                    try:
                        crud.upsert_cached_response(db, normalized_q, personality_used, ai_text)
                    except Exception:
                        pass

                # Update adaptive memory profiles (opt-in + rate-limited).
                try:
                    self._maybe_update_memory(user_id, user_input, ai_text, db, identity_profile, intent, emotion)
                except Exception as e:
                    logger.error(f"Memory update failed: {e}")

                # Update persistent identity profile (pattern-counting, stability threshold).
                try:
                    self._update_identity_profile(db, user_id, identity_profile, emotion, intent)
                except Exception as e:
                    logger.error(f"Identity profile update failed: {e}")
        except Exception as e:
            logger.error(f"Conversation store failed: {e}")

        return {
            "response": ai_text,
            "personality_used": personality_used,
            "session_id": session_id or str(uuid.uuid4()),
            "memory_used": memory_used,
            "personality_info": {"type": personality_used},
            "created_at": created_at_iso,
            "depth_level": depth_level,
            "mode": "fast" if use_fast_mode else "deliberate",
            "intent": intent,
            "emotion": emotion,
            "identity_profile": identity_profile,
            "action_suggestions": action_suggestions,
            "fused_personalities": fused_personalities,
        }


    def switch_personality(
        self,
        personality: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        personality_used = self._determine_personality(user_id, personality, db)
        return {
            "status": "ok",
            "personality_used": personality_used
        }

    def get_available_personalities(self) -> List[Dict[str, str]]:
        return [
            {"type": "default", "name": "Default", "description": "Balanced, helpful assistant"},
            {"type": "mentor", "name": "Mentor", "description": "Guides with experience"},
            {"type": "motivator", "name": "Motivator", "description": "Encouraging and uplifting"},
            {"type": "coach", "name": "Coach", "description": "Action-oriented guidance"},
            {"type": "mitra", "name": "Mitra", "description": "Warm, wise, friendly companion"},
        ]

    def _determine_personality(
        self, 
        user_id: Optional[int], 
        requested_personality: Optional[str], 
        db: Optional[Session]
    ) -> str:
        """Determine which personality to use based on request and user preference."""
        
        # Use requested personality if provided
        if requested_personality and requested_personality in ["default", "mentor", "motivator", "coach", "mitra"]:
            return requested_personality
        
        # Use user's saved preference if available
        if user_id and db:
            user = crud.get_user(db, user_id)
            if user and user.preferred_personality:
                return user.preferred_personality
        
        # Default fallback
        return "default"
    
    def _string_to_personality_enum(self, personality_str: str) -> PersonalityType:
        """Convert string personality to enum."""
        mapping = {
            "default": PersonalityType.DEFAULT,
            "mentor": PersonalityType.MENTOR,
            "motivator": PersonalityType.MOTIVATOR,
            "coach": PersonalityType.COACH,
            "mitra": PersonalityType.MITRA
        }
        return mapping.get(personality_str, PersonalityType.DEFAULT)
    
    def _get_conversation_context(self, user_id: int, db: Session, session_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get recent conversation history for context, scoped to session if provided."""
        try:
            return crud.get_recent_chat_history(db, user_id, limit=8, session_id=session_id)
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []
    
    def _get_memory_context(self, user_input: str, user_id: int, db: Session) -> List[str]:
        """Get relevant long-term memories for context."""
        if not self.long_term_memory:
            return []
        
        try:
            # Retrieve relevant memories based on user input and user opt-ins.
            # Mental health inference is explicitly excluded by consent model.
            allowed_categories = self._get_allowed_memory_categories(user_id, db)
            memories = self.long_term_memory.retrieve_memories(
                user_input,
                user_id,
                top_k=3,
                allowed_categories=allowed_categories,
            )
            return [str(memory) for memory in memories] if memories else []
        except Exception as e:
            logger.error(f"Error getting memory context: {e}")
            return []
    
    def _store_conversation(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        ai_response: str,
        personality_used: str,
        session_id: Optional[str]
    ):
        """Store the conversation in encrypted format and return the DB message."""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            db_msg = crud.create_chat_message(
                db=db,
                user_id=user_id,
                message=user_message,
                response=ai_response,
                personality_used=personality_used,
                session_id=session_id
            )
            return db_msg
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
            return None
    
    def _get_allowed_memory_categories(self, user_id: int, db: Optional[Session]) -> List[str]:
        """Return allowed memory categories based on user opt-in settings."""
        if not db:
            # If we can't read settings, fail safe by returning none.
            return []
        settings_obj = crud.get_user_settings(db, user_id)
        allowed: List[str] = []
        if getattr(settings_obj, "enable_long_term_memory", True):
            if getattr(settings_obj, "allow_preference_learning", True):
                allowed.append("preference")
                allowed.append("identity")
            if getattr(settings_obj, "allow_routine_tracking", True):
                allowed.append("routine")
            if getattr(settings_obj, "allow_mental_health_inference", False):
                allowed.append("mental_health")
        return allowed

    def _maybe_update_memory(
        self,
        user_id: int,
        user_input: str,
        ai_response: str,
        db: Session,
        identity_profile: Optional[Dict[str, Any]] = None,
        intent: str = "general_support",
        emotion: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store lightweight structured memories based on user opt-in and heuristics."""
        if not self.long_term_memory:
            return

        settings_obj = crud.get_user_settings(db, user_id)
        if not getattr(settings_obj, "enable_long_term_memory", True):
            return

        now = datetime.utcnow()
        lowered = (user_input or "").lower()

        preference_keywords = [
            "i like", "i love", "i prefer", "my favorite", "i usually", "i want", "i need", "i enjoy", "i hate", "i wish",
            "when i", "whenever i", "best time", "morning", "evening", "night", "weekends",
        ]
        routine_keywords = [
            "wake", "sleep", "routine", "schedule", "study plan", "every day", "every week", "every month",
            "habit", "calendar", "morning", "evening", "daily", "weekly", "monthly",
        ]

        # Heuristic rate limits to keep vector updates lightweight.
        cooldown = timedelta(minutes=10)

        # Preference memory
        if getattr(settings_obj, "allow_preference_learning", True):
            is_pref_candidate = any(k in lowered for k in preference_keywords)
            if is_pref_candidate:
                last_at = getattr(settings_obj, "last_preference_memory_at", None)
                if last_at is None or (now - last_at) >= cooldown:
                    snippet = user_input.strip()
                    if snippet and len(snippet) <= 500:
                        self.long_term_memory.store_memory_with_category(
                            user_id=user_id,
                            content=f"[preference] {snippet}",
                            memory_type="preference_memory",
                            memory_category="preference",
                        )
                        crud.update_memory_rate_limit_timestamps(db, user_id, update_preference_at=now)

        # Routine memory
        if getattr(settings_obj, "allow_routine_tracking", True):
            is_routine_candidate = any(k in lowered for k in routine_keywords)
            if is_routine_candidate:
                last_at = getattr(settings_obj, "last_routine_memory_at", None)
                if last_at is None or (now - last_at) >= cooldown:
                    snippet = user_input.strip()
                    if snippet and len(snippet) <= 500:
                        self.long_term_memory.store_memory_with_category(
                            user_id=user_id,
                            content=f"[routine] {snippet}",
                            memory_type="routine_memory",
                            memory_category="routine",
                        )
                        crud.update_memory_rate_limit_timestamps(db, user_id, update_routine_at=now)

        # Identity memory (derived behavioral profile)
        if getattr(settings_obj, "allow_preference_learning", True) and identity_profile:
            decision_style = str(identity_profile.get("decision_style", "")).lower()
            current_phase = str(identity_profile.get("current_phase", "")).lower()
            traits = identity_profile.get("core_traits", []) or []
            traits_text = " ".join([str(t).lower() for t in traits])

            # Lightweight candidate gating: only store when user is likely expressing stable traits.
            identity_candidate = any(
                k in (user_input or "").lower()
                for k in ["i tend", "i tend to", "i overthink", "i doubt", "i'm the type", "i always", "i usually", "disciplined", "overthink", "hesitant", "doubt"]
            ) or ("overthinker" in traits_text) or (decision_style in ["hesitant", "clarity_seeking"] and current_phase != "")

            last_at = getattr(settings_obj, "last_preference_memory_at", None)
            if identity_candidate and (last_at is None or (now - last_at) >= cooldown):
                try:
                    payload = json.dumps(identity_profile, ensure_ascii=False)
                except Exception:
                    payload = str(identity_profile)
                snippet = f"[identity] {payload}"
                if snippet and len(snippet) <= 500:
                    self.long_term_memory.store_memory_with_category(
                        user_id=user_id,
                        content=snippet,
                        memory_type="identity_snapshot",
                        memory_category="identity",
                    )
                    crud.update_memory_rate_limit_timestamps(db, user_id, update_preference_at=now)

    def _update_identity_profile(
        self,
        db: Session,
        user_id: int,
        identity_profile: Dict[str, Any],
        emotion: Dict[str, Any],
        intent: str,
    ) -> None:
        """
        Record one observation into the persistent UserIdentityProfile.

        Signal derivation:
          decision_pattern — from hidden_signal (if present) or emotion → decision_style
          energy_cycle     — from identity_profile's session energy_pattern
          core_goal        — from identity_profile's current_phase / core_goal
          new_traits       — from identity_profile's core_traits (session-level)

        The CRUD layer enforces the stability threshold (pattern must repeat ≥2 times
        before being promoted to a stable identity field).
        """
        # --- decision_pattern ---
        hidden = emotion.get("hidden_signal")
        emo = emotion.get("primary_emotion", "neutral")
        decision_pattern: Optional[str] = None
        if hidden in ("overthinking", "hesitation", "burnout", "confusion"):
            decision_pattern = hidden
        elif identity_profile.get("decision_style") == "hesitant":
            decision_pattern = "hesitation"
        elif emo in ("anxious", "stressed"):
            decision_pattern = "overthinking"

        # --- energy_cycle ---
        energy_cycle: Optional[str] = identity_profile.get("energy_pattern") or identity_profile.get("energy_cycle")

        # --- core_goal ---
        core_goal: Optional[str] = identity_profile.get("core_goal") or identity_profile.get("current_phase")

        # --- new_traits ---
        raw_traits = identity_profile.get("core_traits") or []
        # Filter out placeholder values that shouldn't be persisted (see _EPHEMERAL_TRAIT_PLACEHOLDERS)
        new_traits = [t for t in raw_traits if t not in _EPHEMERAL_TRAIT_PLACEHOLDERS]

        crud.observe_identity_signal(
            db,
            user_id,
            decision_pattern=decision_pattern,
            energy_cycle=energy_cycle,
            core_goal=core_goal,
            new_traits=new_traits or None,
        )

    def _normalize_question(self, text: str) -> str:
        """Normalize question text for cache key: lowercase, strip punctuation, collapse spaces."""
        if not text:
            return ""
        lowered = text.lower().strip()
        # Remove punctuation characters for stable keys
        cleaned = re.sub(r"[^a-z0-9\s]", "", lowered)
        # Collapse multiple spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _estimate_conversation_depth(self, user_input: str, recent_messages: List[Dict[str, str]]) -> int:
        """Heuristic to estimate conversation depth level (1-5) for adaptive latency."""
        try:
            length_score = 1 if len(user_input) < 100 else 2 if len(user_input) < 220 else 3
            question_marks = user_input.count('?')
            question_score = 1 if question_marks <= 1 else 2 if question_marks <= 3 else 3
            reflective_keywords = [
                "meaning", "purpose", "feel", "feeling", "why", "anxious", "afraid", "love", "grief",
                "values", "motivation", "relationship", "career", "identity", "conflict", "regret"
            ]
            keyword_hits = sum(1 for k in reflective_keywords if k in user_input.lower())
            keyword_score = 1 if keyword_hits == 0 else 2 if keyword_hits <= 2 else 3

            continuity_score = 1
            try:
                if recent_messages:
                    last = " ".join([str(m.get("content", ""))[:200] for m in recent_messages[-2:]])
                    overlap = sum(1 for k in reflective_keywords if k in last.lower())
                    continuity_score = 1 if overlap == 0 else 2
            except Exception:
                pass

            raw = length_score + question_score + keyword_score + continuity_score
            if raw <= 5:
                return 1
            if raw <= 7:
                return 2
            if raw <= 9:
                return 3
            if raw <= 11:
                return 4
            return 5
        except Exception:
            return 2

# Global instance for use in routes
enhanced_chat_pipeline = EnhancedChatPipeline()
