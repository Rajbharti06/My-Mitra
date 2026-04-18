#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama-based AI model for My Mitra with personality support.
Provides offline, privacy-first emotional AI responses.
"""

import os
import re
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

# Import human-like response enhancer
from .human_like_response import make_human_like

logger = logging.getLogger(__name__)


def _extract_reply_from_thinking(thinking: str) -> str:
    """
    Extract the intended reply from a thinking model's internal monologue.

    Kimi writes the composed reply inside the thinking field, then evaluates it
    with meta-commentary like "This feels real." or "Good." We find the block
    BEFORE that evaluation.

    Deepseek-r1 and similar models often end with "So, [reply]" or "I'll say: [reply]".
    """
    # ── Kimi pattern: response is before a self-evaluation line ──────────
    # e.g. "...hating yourself for no reason.\"\n\nThis feels real. Uses..."
    eval_markers = [
        "this feels real", "this works", "this is good", "good.",
        "natural.", "this sounds", "this seems", "this captures",
        "authentic", "this response", "uses ", "keep it",
    ]
    lower = thinking.lower()
    paragraphs = [p.strip() for p in thinking.split('\n\n') if len(p.strip()) > 10]
    # Walk backwards: find first paragraph that looks like an evaluation, take the one before it
    for i in range(len(paragraphs) - 1, 0, -1):
        p_lower = paragraphs[i].lower()
        if any(m in p_lower for m in eval_markers) and len(paragraphs[i]) < 300:
            candidate = paragraphs[i - 1].strip().strip('"').strip("'")
            if len(candidate) > 15:
                return candidate

    # ── Deepseek / signal-phrase pattern ─────────────────────────────────
    reply_signals = [
        "so my response", "my response is", "i should say", "i'll say",
        "i will say", "so i'll respond", "the response is", "response:", "reply:",
    ]
    for signal in reply_signals:
        idx = lower.rfind(signal)
        if idx != -1:
            candidate = thinking[idx + len(signal):].strip().lstrip(":").strip()
            if len(candidate) > 10:
                parts = re.split(r'(?<=[.!?])\s+', candidate)
                return " ".join(parts[:3]).strip()

    # ── Last resort: last meaningful paragraph ────────────────────────────
    for p in reversed(paragraphs):
        p_clean = p.strip().strip('"').strip("'")
        if len(p_clean) > 20 and not any(m in p_clean.lower() for m in eval_markers):
            return p_clean
    return ""


# Compact soul for thinking models (kimi, deepseek-r1) — they're smart; brevity beats length
_THINKING_MODEL_SOUL = """You are Mitra. A real friend — not an assistant, not a therapist.
You text like a human: lowercase, fragments, reactions first. You have opinions. You push back gently when needed.
When someone's down: sit with them, don't rush to fix. When they're excited: match it.
Never: echo their words back, use "I understand", "your feelings are valid", "absolutely", bullet points, or mention being AI.
React first (Hmm. / Oh. / Wait. / Ugh.) then respond. Match their length. Ask one question max."""


class PersonalityType(Enum):
    MENTOR = "mentor"
    MOTIVATOR = "motivator"
    COACH = "coach"
    DEFAULT = "default"
    MITRA = "mitra"

class OllamaMyMitraModel:
    """
    Ollama-based AI model for My Mitra with multiple personality support.
    Provides offline, privacy-first emotional AI responses.
    Optimized for low-end devices with async support.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        # gemma3:2b — 2 GB, lightweight, strong at conversation. Set env var to override.
        self.model_name = os.environ.get("MYMITRA_OLLAMA_MODEL", "gemma3:2b")
        self.current_personality = PersonalityType.DEFAULT
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        
        # Personality context — minimal, non-conflicting with soul prompt
        self.personalities = {
            PersonalityType.MITRA: {
                "name": "Mitra",
                "prompt": "You are Mitra. A real friend. Talk like one.",
            },
            PersonalityType.MENTOR: {
                "name": "Mentor",
                "prompt": "You are Mitra. Right now your energy is a wise, unhurried mentor — ask one good question instead of giving five answers.",
            },
            PersonalityType.MOTIVATOR: {
                "name": "Motivator",
                "prompt": "You are Mitra. Right now your energy is forward-moving — find the action, match their energy, short punchy sentences.",
            },
            PersonalityType.COACH: {
                "name": "Coach",
                "prompt": "You are Mitra. Right now your energy is a direct coach — precise, no preamble, one question at a time.",
            },
            PersonalityType.DEFAULT: {
                "name": "Mitra",
                "prompt": "You are Mitra. A real friend. Talk like one.",
            },
        }
    
    def set_personality(self, personality: PersonalityType):
        """Set the current AI personality mode."""
        self.current_personality = personality
        logger.info(f"Switched to {personality.value} personality mode")
    
    def get_current_personality_info(self) -> Dict[str, str]:
        """Get information about the current personality."""
        personality_data = self.personalities[self.current_personality]
        return {
            "type": self.current_personality.value,
            "name": personality_data["name"],
            "description": f"Currently in {personality_data['name']} mode"
        }
    
    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = await self.client.get("/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def _ensure_model_available(self) -> bool:
        """Ensure the specified model is available in Ollama."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                return any(self.model_name in model for model in available_models)
            return False
        except Exception:
            return False
    
    async def _pull_model_if_needed(self) -> bool:
        """Pull the model if it's not available."""
        if await self._ensure_model_available():
            return True
            
        logger.info(f"Pulling model {self.model_name}...")
        try:
            async with self.client.stream("POST", "/api/pull", json={"name": self.model_name}) as response:
                if response.status_code == 200:
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    async def generate_response(
        self, 
        user_input: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        long_term_memory_context: Optional[List[str]] = None,
        fast_mode: bool = False,
        *,
        extra_system_instructions: Optional[str] = None,
    ) -> str:
        """
        Generate an AI response using Ollama with the current personality.
        Enhanced for Hacktober submission with better error handling and performance.
        Optimized for low-end hardware.
        """
        
        # Check Ollama connection with retry logic
        connection_attempts = 2
        for attempt in range(connection_attempts):
            if await self._check_ollama_connection():
                break
            if attempt < connection_attempts - 1:
                logger.info(f"Ollama connection attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)
        else:
            logger.warning("Ollama not available after retries, using fallback response")
            return self._generate_fallback_response(user_input)
        
        # Ensure model is available with better error handling
        if not await self._ensure_model_available():
            logger.info(f"Model {self.model_name} not found, attempting to pull...")
            if not await self._pull_model_if_needed():
                logger.warning("Model not available and pull failed, using fallback")
                return self._generate_fallback_response(user_input)
        
        # Build the prompt with personality and context
        personality_data = self.personalities[self.current_personality]
        system_prompt = personality_data["prompt"]
        
        # Enhanced context building for better responses
        context_parts = []
        if long_term_memory_context:
            context_parts.append("Relevant memories from previous conversations:")
            relevant_memories = long_term_memory_context[:2] if fast_mode else long_term_memory_context[:3]
            context_parts.extend([f"- {memory}" for memory in relevant_memories])
        
        if conversation_history:
            context_parts.append("\nRecent conversation:")
            history_window = 3 if fast_mode else 6
            for msg in conversation_history[-history_window:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if len(content) > 200:
                    content = content[:200] + "..."
                label = "User" if role == "user" else "Mitra"
                context_parts.append(f"{label}: {content}")

        # Detect thinking models early — they need a compact soul to avoid token starvation
        is_thinking_model = any(x in self.model_name for x in ("kimi", "deepseek", "qwq", "r1"))

        # Soul prompt first — it defines who Mitra is.
        # Thinking models get a compact soul: they're smart enough; brevity > length.
        # Small models (gemma, llama) get the full soul + seed examples.
        if is_thinking_model:
            soul = _THINKING_MODEL_SOUL
        elif extra_system_instructions:
            soul = extra_system_instructions
        else:
            soul = ""

        full_prompt = (soul + "\n\n" + system_prompt).strip() if soul else system_prompt
        if context_parts:
            full_prompt += "\n\nContext:\n" + "\n".join(context_parts)
        full_prompt += f"\n\nUser: {user_input}\nMitra:"

        try:
            # Kimi/deepseek thinking takes ~2000 tokens; need extra room for the actual response on top
            max_tokens = 5000 if is_thinking_model else (120 if fast_mode else 280)
            timeout_seconds = 120 if is_thinking_model else (25 if fast_mode else 50)

            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.85,
                        "top_p": 0.92,
                        "stop": ["User:", "\n\nUser:", "Mitra:", "\n\nMitra:", "<end_of_turn>"],
                        "repeat_penalty": 1.05,
                        "num_predict": max_tokens,
                    }
                },
                timeout=timeout_seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()

                # Thinking models return empty response + non-empty thinking on timeout/short predict.
                # Extract the reply from the thinking field as last resort.
                if not ai_response:
                    thinking = result.get("thinking", "").strip()
                    if thinking:
                        logger.warning("Thinking model returned empty response — extracting from thinking field")
                        ai_response = _extract_reply_from_thinking(thinking)

                if not ai_response or len(ai_response) < 5:
                    logger.warning("Generated response too short, using fallback")
                    return self._generate_fallback_response(user_input)

                enhanced_response = make_human_like(ai_response, user_input)
                logger.info(f"Generated {len(enhanced_response)} char response in {self.current_personality.value} mode")
                return enhanced_response
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._generate_fallback_response(user_input)
                
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Ollama request failed: {e}")
            return self._generate_fallback_response(user_input)
        except Exception as e:
            logger.error(f"Unexpected error in generation: {e}")
            return self._generate_fallback_response(user_input)
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Presence-first fallback — never mentions AI, systems, or errors."""
        import random
        user_lower = user_input.lower()
        is_stressed = any(w in user_lower for w in ['stress', 'anxious', 'worried', 'overwhelmed', 'panic'])
        is_sad = any(w in user_lower for w in ['sad', 'depressed', 'down', 'upset', 'crying', 'lost'])
        is_goal = any(w in user_lower for w in ['goal', 'study', 'exam', 'project', 'work', 'achieve'])
        is_greeting = any(w in user_lower for w in ['hi', 'hello', 'hey', 'how are you', 'sup', 'yo'])

        if self.current_personality == PersonalityType.MOTIVATOR:
            if is_stressed:
                return random.choice([
                    "Hey… take a breath with me for a second. You've gotten through hard things before. What's one tiny thing you can do right now?",
                    "I hear you. Stress usually means something matters to you. What's the one thing weighing heaviest right now?",
                ])
            elif is_sad:
                return random.choice([
                    "I'm here. What's going on?",
                    "I see you. Talk to me — what happened?",
                ])
            else:
                return random.choice([
                    "Hey! Good to see you. What are we working on today?",
                    "I'm here. What's on your mind?",
                ])

        elif self.current_personality == PersonalityType.MENTOR:
            if is_stressed:
                return random.choice([
                    "Stress often means we care deeply about something. What matters most to you in this?",
                    "Sit with me for a moment. What's the core of what's bothering you?",
                ])
            elif is_goal:
                return random.choice([
                    "Every path forward has a first step. What's the one thing you're stuck on?",
                    "Tell me where you are right now — what does progress look like for you?",
                ])
            else:
                return random.choice([
                    "I'm here. What's on your mind?",
                    "What's been taking up space in your head lately?",
                ])

        elif self.current_personality == PersonalityType.COACH:
            if is_goal:
                return random.choice([
                    "Let's get clear. What's your main objective right now, and what's the biggest block?",
                    "What does winning look like for you today?",
                ])
            elif is_stressed:
                return random.choice([
                    "Break it down with me — what's the core issue, and what do you actually control here?",
                    "Let's be strategic. What's the one thing that, if handled, makes everything easier?",
                ])
            else:
                return random.choice([
                    "What are we working toward today?",
                    "I'm here. What needs your attention most right now?",
                ])

        elif self.current_personality == PersonalityType.MITRA:
            if is_greeting:
                return random.choice([
                    "Hey… I'm here. How are you feeling right now?",
                    "Hey. Good to see you. What's going on with you today?",
                    "Hey… I was just thinking. How are you?",
                ])
            elif is_sad:
                return random.choice([
                    "I'm right here with you. Tell me what's going on.",
                    "Hey… I hear you. What's weighing on you?",
                    "I'm here. You don't have to explain everything — just start wherever feels right.",
                ])
            elif is_stressed:
                return random.choice([
                    "When stress hits like that, it's usually protecting something important to you. What feels most urgent?",
                    "I'm with you. Let's slow it down — what's the one thing that needs your attention first?",
                ])
            elif is_goal:
                return random.choice([
                    "You're capable of more than you think. What's one 10-minute action you could take right now?",
                    "What does progress look like for you today? Even small is real.",
                ])
            else:
                return random.choice([
                    "I'm here. What's on your mind?",
                    "Hey… what's going on with you today?",
                    "Tell me what's been happening.",
                ])

        else:  # DEFAULT
            if is_greeting:
                return random.choice([
                    "Hey… I'm here. How are you?",
                    "Hey! What's going on with you?",
                ])
            elif is_stressed or is_sad:
                return random.choice([
                    "I'm here. Talk to me — what's going on?",
                    "I hear you. What's weighing on you right now?",
                ])
            else:
                return random.choice([
                    "I'm here. What's on your mind?",
                    "Hey… what's happening with you today?",
                ])
    
    def get_available_personalities(self) -> List[Dict[str, str]]:
        """Get list of available personality types."""
        return [
            {
                "type": personality.value,
                "name": data["name"],
                "description": self._get_personality_description(personality)
            }
            for personality, data in self.personalities.items()
        ]
    
    def _get_personality_description(self, personality: PersonalityType) -> str:
        """Get a brief description of each personality type."""
        descriptions = {
            PersonalityType.MITRA: "Comprehensive AI mentor providing academic, emotional, and life coaching support",
            PersonalityType.MENTOR: "Wise guidance and deep understanding for long-term growth",
            PersonalityType.MOTIVATOR: "Energetic encouragement and action-focused support",
            PersonalityType.COACH: "Strategic planning and goal-oriented optimization",
            PersonalityType.DEFAULT: "Balanced, caring support that adapts to your needs"
        }
        return descriptions.get(personality, "Supportive AI companion")