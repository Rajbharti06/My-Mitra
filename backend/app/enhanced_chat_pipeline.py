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
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from llm.ollama_model import OllamaMyMitraModel, PersonalityType
from vector_memory import LongTermMemory
from . import crud

logger = logging.getLogger(__name__)

class EnhancedChatPipeline:
    """Enhanced chat pipeline with personality, memory, and caching."""

    def __init__(self):
        self.model = OllamaMyMitraModel()
        try:
            self.long_term_memory = LongTermMemory()
        except Exception:
            self.long_term_memory = None

    def get_mitra_reply(
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
        else:
            # Generate response via model
            ai_text = self.model.generate_response(user_input, personality_type, context_messages)
            memory_used = bool(context_messages)

        # Persist conversation if authenticated
        try:
            if user_id and db:
                self._store_conversation(db, user_id, user_input, ai_text, personality_used, session_id)
        except Exception as e:
            logger.error(f"Conversation store failed: {e}")

        return {
            "response": ai_text,
            "personality_used": personality_used,
            "session_id": session_id or str(uuid.uuid4()),
            "memory_used": memory_used,
            "personality_info": {"type": personality_used}
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
    
    def _get_memory_context(self, user_input: str, user_id: int) -> List[str]:
        """Get relevant long-term memories for context."""
        if not self.long_term_memory:
            return []
        
        try:
            # Retrieve relevant memories based on user input
            memories = self.long_term_memory.retrieve_memories(user_input, user_id, top_k=3)
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
        """Store the conversation in encrypted format."""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            crud.create_chat_message(
                db=db,
                user_id=user_id,
                message=user_message,
                response=ai_response,
                personality_used=personality_used,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    def _update_memory(self, user_id: int, user_input: str, ai_response: str):
        """Update long-term memory with the conversation."""
        if not self.long_term_memory:
            return
        
        try:
            # Store both user input and AI response for context
            self.long_term_memory.store_memory(
                user_id=user_id,
                content=f"User: {user_input}\nMyMitra: {ai_response}",
                memory_type="conversation"
            )
        except Exception as e:
            logger.error(f"Error updating memory: {e}")

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

# Global instance for use in routes
enhanced_chat_pipeline = EnhancedChatPipeline()