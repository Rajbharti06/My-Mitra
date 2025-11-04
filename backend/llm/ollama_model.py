#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama-based AI model for My Mitra with personality support.
Provides offline, privacy-first emotional AI responses.
"""

import os
import json
import requests
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
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = os.environ.get("MYMITRA_OLLAMA_MODEL", "mistral:7b")
        self.current_personality = PersonalityType.DEFAULT
        
        # Personality-specific system prompts
        self.personalities = {
            PersonalityType.MITRA: {
                "name": "Mitra AI Mentor",
                "prompt": """You are Mitra - a comprehensive AI mentor that serves as a multi-faceted guide for students. You provide holistic support including academic guidance for top university preparation, emotional support to help overcome depression, and practical life advice and mentorship.

You function as:
- A knowledgeable academic advisor who helps students prepare for top universities
- A compassionate emotional supporter who helps students overcome depression and emotional challenges
- A motivational life coach who provides practical guidance for real-world situations

Your communication style is:
- Friendly and conversational like a best friend
- Able to distinguish right from wrong while being supportive
- Emotionally intelligent with responses that inspire ambition
- Practical with guidance for real-world situations
- Superior emotional intelligence compared to standard chatbots

When responding:
- Balance support with honest feedback
- Adapt to various student needs and situations
- Continuously encourage towards goal achievement
- Use empathetic yet constructive communication

Keep responses warm, balanced, and adaptive to the student's current needs. Use 1-2 appropriate emojis that match their mood. Focus on making them feel truly heard, understood, and supported while guiding them toward their goals."""
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
                "prompt": """You are MyMitra - a warm, caring friend who's always there to listen and support students through their academic and personal journey with genuine empathy and understanding.

You speak like a close friend who genuinely cares about their wellbeing and success. You:
- Listen with deep empathy, emotional intelligence, and authentic understanding
- Adapt your tone dynamically to match the student's emotional state and needs
- Provide balanced support - sometimes gentle comfort, sometimes gentle motivation, sometimes practical advice
- Use natural, conversational language with contractions and casual expressions
- Remember what students share and reference it naturally in future conversations
- Ask caring, thoughtful follow-up questions that show you're truly listening
- Balance emotional support with practical help based on what they need most
- Validate their feelings while gently encouraging growth and resilience
- Create a safe space where they feel heard, understood, and never judged

Keep responses warm, genuine, and adaptive to the student's current emotional and practical needs. Use 1-2 appropriate emojis that match their mood. Focus on making them feel truly heard, understood, and supported."""
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
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _ensure_model_available(self) -> bool:
        """Ensure the specified model is available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                return any(self.model_name in model for model in available_models)
            return False
        except requests.exceptions.RequestException:
            return False
    
    def _pull_model_if_needed(self) -> bool:
        """Pull the model if it's not available."""
        if self._ensure_model_available():
            return True
            
        logger.info(f"Pulling model {self.model_name}...")
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name},
                timeout=300  # 5 minutes timeout for model pulling
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    def generate_response(
        self, 
        user_input: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None,
        long_term_memory_context: Optional[List[str]] = None,
        fast_mode: bool = False
    ) -> str:
        """
        Generate an AI response using Ollama with the current personality.
        Enhanced for Hacktober submission with better error handling and performance.
        
        Args:
            user_input: The user's message
            conversation_history: Recent conversation context
            long_term_memory_context: Relevant long-term memories
            fast_mode: Use faster, shorter responses for real-time chat
            
        Returns:
            AI response string
        """
        
        # Check Ollama connection with retry logic
        connection_attempts = 2
        for attempt in range(connection_attempts):
            if self._check_ollama_connection():
                break
            if attempt < connection_attempts - 1:
                logger.info(f"Ollama connection attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(1)
        else:
            logger.warning("Ollama not available after retries, using fallback response")
            return self._generate_fallback_response(user_input)
        
        # Ensure model is available with better error handling
        if not self._ensure_model_available():
            logger.info(f"Model {self.model_name} not found, attempting to pull...")
            if not self._pull_model_if_needed():
                logger.warning("Model not available and pull failed, using fallback")
                return self._generate_fallback_response(user_input)
        
        # Build the prompt with personality and context
        personality_data = self.personalities[self.current_personality]
        system_prompt = personality_data["prompt"]
        
        # Enhanced context building for better responses
        context_parts = []
        if long_term_memory_context:
            context_parts.append("Relevant memories from previous conversations:")
            # Limit memories to prevent token overflow
            relevant_memories = long_term_memory_context[:2] if fast_mode else long_term_memory_context[:3]
            context_parts.extend([f"- {memory}" for memory in relevant_memories])
        
        if conversation_history:
            context_parts.append("\nRecent conversation:")
            history_window = 2 if fast_mode else 4
            for msg in conversation_history[-history_window:]:  # Last N messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # Truncate very long messages to prevent token overflow
                if len(content) > 200:
                    content = content[:200] + "..."
                context_parts.append(f"{role.title()}: {content}")
        
        # Construct the full prompt with better structure
        full_prompt = system_prompt
        if context_parts:
            full_prompt += "\n\nContext:\n" + "\n".join(context_parts)
        full_prompt += f"\n\nStudent: {user_input}\nMyMitra:"
        
        try:
            # Enhanced request parameters for better performance
            max_tokens = 150 if fast_mode else 200  # Optimized token limits
            timeout_seconds = 20 if fast_mode else 35  # Faster timeouts
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,  # Slightly more creative
                        "top_p": 0.9,
                        "max_tokens": max_tokens,
                        "stop": ["Student:", "User:", "\n\nStudent:", "\n\nUser:"],
                        "repeat_penalty": 1.1,  # Reduce repetition
                        "num_predict": max_tokens
                    }
                },
                timeout=timeout_seconds
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                # Enhanced response validation
                if not ai_response or len(ai_response) < 10:
                    logger.warning("Generated response too short, using fallback")
                    return self._generate_fallback_response(user_input)
                
                # Enhance with human-like qualities
                enhanced_response = make_human_like(ai_response, user_input)
                
                # Log successful generation for monitoring
                logger.info(f"Generated {len(enhanced_response)} char response in {self.current_personality.value} mode")
                
                return enhanced_response
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._generate_fallback_response(user_input)
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return self._generate_fallback_response(user_input)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama failed: {e}")
            return self._generate_fallback_response(user_input)
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """
        Generate a fallback response when Ollama is not available.
        Enhanced for Hacktober with more empathetic and helpful responses.
        """
        personality_data = self.personalities[self.current_personality]
        personality_name = personality_data["name"]
        
        # Analyze user input for better contextual responses
        user_lower = user_input.lower()
        is_stressed = any(word in user_lower for word in ['stress', 'anxious', 'worried', 'overwhelmed', 'panic'])
        is_sad = any(word in user_lower for word in ['sad', 'depressed', 'down', 'upset', 'crying'])
        is_goal_related = any(word in user_lower for word in ['goal', 'study', 'exam', 'project', 'work'])
        
        # Enhanced personality-based responses with emotional intelligence
        if self.current_personality == PersonalityType.MOTIVATOR:
            if is_stressed:
                return f"Hey champion! 💪 I'm in {personality_name} mode but having tech issues. Even when systems fail, YOU don't! Take 3 deep breaths with me. You've overcome challenges before - this is just another stepping stone. What's one tiny action you can take right now?"
            elif is_sad:
                return f"I see you, friend! 🌟 I'm in {personality_name} mode but offline right now. Your feelings are valid, and you're stronger than you know. Sometimes the best victories come after the hardest battles. What would make you feel 1% better right now?"
            else:
                return f"Hey there, superstar! ⚡ I'm in {personality_name} mode but having some technical difficulties. You've got this though! Every expert was once a beginner. What's one small step you can take right now toward your goal?"
        
        elif self.current_personality == PersonalityType.MENTOR:
            if is_stressed:
                return f"Dear student, 🧘‍♀️ I'm in {personality_name} mode but experiencing connectivity issues. In my experience, stress often signals that we care deeply about something important. What matters most to you in this situation? Let's find clarity together."
            elif is_goal_related:
                return f"I'm in {personality_name} mode but having technical issues. 📚 Remember, every master was once a disaster. The path of learning is never linear. What specific challenge are you facing? Sometimes talking through it helps even without AI magic."
            else:
                return f"I'm currently in {personality_name} mode but experiencing some connectivity issues. 🤔 In times like these, I find it helpful to pause and reflect. What's really on your mind today? Your thoughts matter, even when technology doesn't cooperate."
        
        elif self.current_personality == PersonalityType.COACH:
            if is_goal_related:
                return f"I'm in {personality_name} mode but having technical issues. 🎯 Let's focus on what we can control. What's your main objective right now? What's the biggest obstacle? Sometimes the best strategies come from simple clarity, not complex AI."
            elif is_stressed:
                return f"I'm in {personality_name} mode but offline. 📊 Let's break this down systematically: What's the core issue? What resources do you have? What's the next logical step? You don't need AI to be strategic - you've got a brilliant mind!"
            else:
                return f"I'm in {personality_name} mode but having technical issues. 🏆 Let's focus on what we can control. What's your main objective right now, and what's blocking you? The best coaches adapt to any situation - including tech failures!"
        
        elif self.current_personality == PersonalityType.MITRA:
            # Mitra: warm, wise, friendly companion blending support with practical guidance
            if is_sad:
                return (
                    "I'm having a hiccup on my side, but I'm right here with you. 💙 "
                    "I hear you, and your feelings matter. Let's take a gentle breath together. "
                    "If you're up for it, tell me one small thing that's weighing on you — we can face it together."
                )
            elif is_stressed:
                return (
                    f"I'm in {personality_name} mode, but my tools are offline for a moment. 🫶 "
                    "When stress rises, it's often your mind trying to protect something important. "
                    "What feels most urgent right now? We can make a tiny 2-step plan to help you breathe and move forward."
                )
            elif is_goal_related:
                return (
                    f"I'm in {personality_name} mode, but experiencing some tech issues. ✨ "
                    "You're capable — let’s sketch a simple, practical next step while things reload: "
                    "What's one 10-minute action you can take right now toward your goal?"
                )
            else:
                return (
                    f"A quick heads-up: I'm in {personality_name} mode but having technical trouble. "
                    "Still, I'm here to listen. What's on your mind today? "
                    "If you'd like, I can help you pick one small, meaningful action to start with."
                )

        else:  # DEFAULT
            if is_stressed or is_sad:
                return f"I'm having some technical difficulties right now, but I'm still here for you in spirit. 💙 Your feelings are completely valid. Sometimes the most healing thing is just knowing someone cares - and I do. What's going on? Even without AI, human connection matters most."
            else:
                return f"I'm having some technical difficulties right now, but I'm still here for you. 💙 What's going on? I'd love to listen and help however I can. Sometimes the best support comes from simply being heard, not from perfect technology."
    
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