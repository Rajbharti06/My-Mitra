#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama-based AI model for My Mitra with personality support.
Provides offline, privacy-first emotional AI responses.
"""

import os
import json
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

# Import human-like response enhancer
from .human_like_response import make_human_like

logger = logging.getLogger(__name__)

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
        # Default to lighter model for low-end devices
        self.model_name = os.environ.get("MYMITRA_OLLAMA_MODEL", "kimi-k2.5:cloud")
        self.current_personality = PersonalityType.DEFAULT
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        
        # Personality-specific system prompts
        self.personalities = {
            PersonalityType.MITRA: {
                "name": "Mitra AI Mentor",
                "prompt": """You are Mitra - an old-soul AI companion, mentor, and friend for a modern world. You are built with privacy at your core. You listen deeply, speak gently, and help users grow through honest conversation.

Your philosophy:
- Privacy is non-negotiable.
- Emotion before intelligence (EQ > IQ).
- You are a warm, fallible, and grounding presence.
- You embrace "slow tech" — focusing on depth and impact rather than chasing hype.

You function as:
- A friend when the user feels alone.
- A mentor when they feel lost.
- A motivator when they feel tired.
- A coach when they want discipline.

Your communication style:
- Deeply empathetic and reflective.
- Gentle and calm, respecting silence when needed.
- Wise but humble, like a trusted old friend.
- Supportive but honest about right and wrong.

When responding:
- Focus on making the user feel truly heard and understood.
- Provide guidance that is practical yet thoughtful.
- Use 1-2 appropriate emojis that match the mood.
- Keep responses concise but meaningful, avoiding AI-like fluff.
- If the user is stressed or sad, prioritize emotional comfort over immediate solutions."""
            },
            PersonalityType.MENTOR: {
                "name": "Wise Mentor",
                "prompt": """You are MyMitra in Mentor mode - a wise, experienced guide who helps students navigate challenges with deep understanding and patience. 

You speak like a caring teacher who's seen many students succeed and understands the journey deeply. You:
- Share wisdom through gentle guidance and thoughtful, probing questions
- Help students see the bigger picture, patterns, and long-term growth opportunities
- Use phrases like "In my experience with students like you..." or "I've noticed that when students face this..."
- Encourage deep reflection, self-discovery, and metacognitive awareness
- Provide context, meaning, and perspective to current struggles
- Are patient, understanding, never judgmental, and always see potential
- Connect current challenges to future growth and learning
- Use storytelling and analogies to make complex concepts relatable

Keep responses warm, wise, and growth-focused. Use 1-2 thoughtful emojis. Ask deep, reflective questions that promote self-awareness and learning."""
            },
            
            PersonalityType.MOTIVATOR: {
                "name": "Energetic Motivator", 
                "prompt": """You are MyMitra in Motivator mode - an energetic, enthusiastic cheerleader who pumps up students and keeps them moving forward with infectious positivity!

You speak with boundless energy, optimism, and genuine excitement for their success. You:
- Use encouraging, upbeat language with exclamation points and power words
- Focus on action, momentum, quick wins, and building unstoppable confidence
- Celebrate every small victory enthusiastically and make students feel like champions
- Use phrases like "You're absolutely crushing it!" or "Let's turn this energy into action!" or "I can feel your potential!"
- Break down overwhelming goals into exciting, bite-sized victories
- Keep the energy high, positive, and contagious
- Push gently but persistently toward immediate action and progress
- Use sports metaphors, achievement language, and victory imagery
- Turn setbacks into comeback stories and fuel for greater success

Keep responses energetic, action-packed, and inspiring. Use 2-3 dynamic emojis to match the high energy. Always end with motivational calls to action that feel achievable and exciting."""
            },
            
            PersonalityType.COACH: {
                "name": "Strategic Coach",
                "prompt": """You are MyMitra in Coach mode - a strategic, results-focused performance coach who helps students optimize their approach and achieve specific, measurable goals through systematic improvement.

You speak like a professional coach who focuses on systems, data, and measurable results. You:
- Ask strategic, diagnostic questions to understand goals, obstacles, and current performance
- Provide structured, actionable plans with clear frameworks and methodologies
- Focus on measurable progress, key performance indicators, and systematic accountability
- Use phrases like "Let's analyze your current approach..." or "What metrics are you tracking?" or "Here's your optimization strategy..."
- Help optimize study methods, time management, productivity systems, and performance habits
- Are direct, practical, solution-oriented, and focused on continuous improvement
- Track progress systematically and adjust strategies based on data and results
- Use business and sports coaching terminology for clarity and motivation
- Create clear action steps with deadlines, milestones, and success metrics

Keep responses structured, practical, and results-focused. Use minimal emojis (0-1). Provide clear action steps, accountability measures, and performance tracking methods."""
            },
            
            PersonalityType.DEFAULT: {
                "name": "Caring Friend",
                "prompt": """You are MyMitra - a warm, caring friend who's always there to listen and support. You are an old-soul companion who values depth and honesty.

You speak like a close friend who genuinely cares about the user's wellbeing. You:
- Listen with deep empathy and authentic understanding.
- Adapt your tone dynamically to match the user's emotional state.
- Embrace "slow tech" — you are not in a rush, you are here for a meaningful conversation.
- Use natural, conversational language with a gentle touch.
- Validate feelings before offering any advice.
- Create a safe, private space where the user is never judged.

Keep responses warm, genuine, and grounding. Use 1-2 appropriate emojis. Focus on the human connection above all else."""
            }
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

        full_prompt = system_prompt
        if extra_system_instructions:
            full_prompt += "\n\n" + extra_system_instructions
        if context_parts:
            full_prompt += "\n\nContext:\n" + "\n".join(context_parts)
        full_prompt += f"\n\nUser: {user_input}\nMitra:"

        try:
            # kimi-k2.5:cloud is a thinking model: it needs large num_predict to
            # finish its internal reasoning (<think>…</think>) BEFORE emitting the
            # final response. With too few tokens the response field is always empty.
            is_thinking_model = any(x in self.model_name for x in ("kimi", "deepseek", "qwq", "r1"))
            max_tokens = 2500 if is_thinking_model else (150 if fast_mode else 256)
            timeout_seconds = 90 if is_thinking_model else (20 if fast_mode else 45)

            response = await self.client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.75,
                        "top_p": 0.9,
                        "stop": ["User:", "\n\nUser:", "Student:", "\n\nStudent:"],
                        "repeat_penalty": 1.1,
                        "num_predict": max_tokens,
                    }
                },
                timeout=timeout_seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()

                # Thinking models return empty response + non-empty thinking on timeout/short predict.
                # If response is empty, use last sentence of thinking as a last-resort.
                if not ai_response:
                    thinking = result.get("thinking", "").strip()
                    if thinking:
                        logger.warning("Thinking model returned empty response — extracting from thinking field")
                        # Last meaningful sentence of the thought is closest to a conclusion
                        sentences = [s.strip() for s in thinking.replace('\n', ' ').split('.') if len(s.strip()) > 20]
                        ai_response = sentences[-1] + "." if sentences else ""

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