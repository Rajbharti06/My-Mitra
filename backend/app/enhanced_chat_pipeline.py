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
    """
    Enhanced chat pipeline that integrates Ollama AI with personality support,
    long-term memory, and encrypted chat storage.
    """
    
    def __init__(self):
        self.ollama_model = OllamaMyMitraModel()
        self.long_term_memory = LongTermMemory() if not os.environ.get("MYMITRA_ECHO_ONLY") else None
        self.echo_only = os.environ.get("MYMITRA_ECHO_ONLY") == "1"
        
    def get_mitra_reply(
        self,
        user_input: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        personality: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from My Mitra with personality and memory support.
        
        Args:
            user_input: The user's message
            user_id: User ID for personalization and storage
            db: Database session for storing chat history
            personality: Specific personality to use (overrides user preference)
            session_id: Session ID for grouping conversations
            
        Returns:
            Dictionary containing response and metadata
        """
        
        # Handle echo-only mode for testing
        if self.echo_only:
            return {
                "response": f"[ECHO MODE] You said: {user_input}",
                "personality_used": personality or "default",
                "session_id": session_id,
                "memory_used": False
            }
        
        try:
            # Determine personality to use
            active_personality = self._determine_personality(user_id, personality, db)
            
            # Set the AI model personality
            personality_enum = self._string_to_personality_enum(active_personality)
            self.ollama_model.set_personality(personality_enum)
            
            # Get conversation context
            conversation_history = self._get_conversation_context(user_id, db) if user_id and db else []
            
            # Get long-term memory context
            memory_context = self._get_memory_context(user_input, user_id) if user_id else []

            # Try fast cache path for general FAQs (no personal context)
            question_key = self._normalize_question(user_input)
            ai_response = None
            cache_used = False
            if db and not memory_context and not conversation_history:
                cached = crud.get_cached_response(db, question_key, active_personality)
                if cached:
                    ai_response = cached
                    cache_used = True
            
            # Generate AI response (fast mode prioritized) if cache miss
            if ai_response is None:
                ai_response = self.ollama_model.generate_response(
                    user_input=user_input,
                    conversation_history=conversation_history,
                    long_term_memory_context=memory_context,
                    fast_mode=True
                )
            
            # Store the conversation if user is logged in
            if user_id and db:
                self._store_conversation(
                    db=db,
                    user_id=user_id,
                    user_message=user_input,
                    ai_response=ai_response,
                    personality_used=active_personality,
                    session_id=session_id
                )
                
                # Update long-term memory
                if self.long_term_memory:
                    self._update_memory(user_id, user_input, ai_response)
            
            result = {
                "response": ai_response,
                "personality_used": active_personality,
                "session_id": session_id,
                "memory_used": len(memory_context) > 0,
                "personality_info": self.ollama_model.get_current_personality_info(),
                "cache_used": cache_used
            }

            # Persist a cache entry for general FAQs (no personal context)
            if db and not memory_context and not conversation_history and not cache_used:
                try:
                    crud.upsert_cached_response(db, question_key, active_personality, ai_response)
                except Exception:
                    pass

            return result
            
        except Exception as e:
            logger.error(f"Error in chat pipeline: {e}")
            return {
                "response": "I'm having some technical difficulties right now, but I'm still here for you. Could you try again? 💙",
                "personality_used": personality or "default",
                "session_id": session_id,
                "memory_used": False,
                "error": str(e)
            }
    
    def switch_personality(
        self,
        personality: str,
        user_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Switch the AI personality and optionally save as user preference.
        
        Args:
            personality: New personality type
            user_id: User ID to save preference
            db: Database session
            
        Returns:
            Dictionary with personality info and success status
        """
        try:
            # Validate personality
            if personality not in ["default", "mentor", "motivator", "coach"]:
                return {
                    "success": False,
                    "error": "Invalid personality type",
                    "available_personalities": self.get_available_personalities()
                }
            
            # Set the personality
            personality_enum = self._string_to_personality_enum(personality)
            self.ollama_model.set_personality(personality_enum)
            
            # Save as user preference if logged in
            if user_id and db:
                crud.update_user_personality(db, user_id, personality)
            
            return {
                "success": True,
                "personality_info": self.ollama_model.get_current_personality_info(),
                "message": f"Switched to {personality} mode! 🎭"
            }
            
        except Exception as e:
            logger.error(f"Error switching personality: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_personalities(self) -> List[Dict[str, str]]:
        """Get list of available AI personalities."""
        return self.ollama_model.get_available_personalities()
    
    def _determine_personality(
        self, 
        user_id: Optional[int], 
        requested_personality: Optional[str], 
        db: Optional[Session]
    ) -> str:
        """Determine which personality to use based on request and user preference."""
        
        # Use requested personality if provided
        if requested_personality and requested_personality in ["default", "mentor", "motivator", "coach"]:
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
            "coach": PersonalityType.COACH
        }
        return mapping.get(personality_str, PersonalityType.DEFAULT)
    
    def _get_conversation_context(self, user_id: int, db: Session) -> List[Dict[str, str]]:
        """Get recent conversation history for context."""
        try:
            return crud.get_recent_chat_history(db, user_id, limit=8)
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