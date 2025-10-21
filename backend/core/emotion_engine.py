"""
Emotion Engine - Core module for emotion detection and analysis
MyMitra's emotion-adaptive AI system that detects and responds to user emotions
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import os
from pathlib import Path

# Try to import TextBlob for sentiment analysis, with fallback
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob not available. Using rule-based fallback for sentiment analysis.")

# Try to import HuggingFace transformers for more advanced emotion detection
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Using rule-based fallback for emotion detection.")

class EmotionCategory(str, Enum):
    """Emotion categories detected by the engine"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    STRESSED = "stressed"
    CONFUSED = "confused"
    NEUTRAL = "neutral"
    MOTIVATED = "motivated"

class EmotionIntensity(str, Enum):
    """Intensity levels for detected emotions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EmotionEngine:
    """
    Core emotion detection and analysis engine for MyMitra
    Provides multi-layered emotion detection using:
    1. Rule-based keyword matching (always available)
    2. TextBlob sentiment analysis (if available)
    3. HuggingFace transformer models (if available)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the emotion engine with available detection methods
        
        Args:
            model_path: Optional path to a local HuggingFace model
        """
        self.logger = logging.getLogger(__name__)
        
        # Load emotion keywords and patterns
        self._load_emotion_patterns()
        
        # Initialize TextBlob if available
        self.textblob_available = TEXTBLOB_AVAILABLE
        
        # Initialize transformer pipeline if available
        self.transformer_available = TRANSFORMERS_AVAILABLE
        self.emotion_classifier = None
        
        if TRANSFORMERS_AVAILABLE and model_path:
            try:
                # Try to load local model if specified
                self.emotion_classifier = pipeline(
                    "text-classification", 
                    model=model_path,
                    return_all_scores=True
                )
                self.logger.info(f"Loaded local emotion model from {model_path}")
            except Exception as e:
                self.logger.error(f"Failed to load local model: {e}")
                self._try_load_default_model()
        elif TRANSFORMERS_AVAILABLE:
            self._try_load_default_model()
    
    def _try_load_default_model(self):
        """Try to load a small default emotion model"""
        try:
            # Use a small emotion classification model
            self.emotion_classifier = pipeline(
                "text-classification", 
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            self.logger.info("Loaded default emotion model")
        except Exception as e:
            self.logger.error(f"Failed to load default emotion model: {e}")
            self.transformer_available = False
    
    def _load_emotion_patterns(self):
        """Load emotion keywords and patterns from internal dictionary"""
        # Dictionary mapping emotions to their keywords and phrases
        self.emotion_patterns = {
            EmotionCategory.HAPPY: {
                'keywords': [
                    r'\bhappy\b', r'\bjoy\b', r'\bexcited\b', r'\bgreat\b', r'\bamazing\b',
                    r'\bwonderful\b', r'\bdelighted\b', r'\bpleased\b', r'\bglad\b', r'\bcheerful\b',
                    r'\bthankful\b', r'\bgrateful\b', r'\bblessed\b', r'\bproud\b', r'\bsatisfied\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bincredibly\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.SAD: {
                'keywords': [
                    r'\bsad\b', r'\bunhappy\b', r'\bupset\b', r'\bdepressed\b', r'\bheartbroken\b',
                    r'\bdown\b', r'\bmiserable\b', r'\bdisappointed\b', r'\bregret\b', r'\bsorry\b',
                    r'\blonely\b', r'\bhopeless\b', r'\bgrief\b', r'\bmelancholy\b', r'\bblue\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bdeeply\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.ANGRY: {
                'keywords': [
                    r'\bangry\b', r'\bfurious\b', r'\bmad\b', r'\birritated\b', r'\bannoyed\b',
                    r'\bfrustrated\b', r'\benraged\b', r'\bupset\b', r'\boffended\b', r'\bresentful\b',
                    r'\bhostile\b', r'\bhateful\b', r'\binfuriated\b', r'\bpissed\b', r'\bagitated\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bfucking\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.ANXIOUS: {
                'keywords': [
                    r'\banxious\b', r'\bnervous\b', r'\bworried\b', r'\bfearful\b', r'\bscared\b',
                    r'\bafraid\b', r'\bpanicked\b', r'\buneasy\b', r'\bdistressed\b', r'\bconcerned\b',
                    r'\bapprehensive\b', r'\bdread\b', r'\btense\b', r'\bterrified\b', r'\bfrightened\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bterribly\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.STRESSED: {
                'keywords': [
                    r'\bstressed\b', r'\boverwhelmed\b', r'\bexhausted\b', r'\btired\b', r'\bburnt out\b',
                    r'\bpressured\b', r'\boverloaded\b', r'\bbusy\b', r'\bchaotic\b', r'\bhectic\b',
                    r'\bstrain\b', r'\btoo much\b', r'\bcan\'t handle\b', r'\bstruggling\b', r'\bdifficult\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bcompletely\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.CONFUSED: {
                'keywords': [
                    r'\bconfused\b', r'\bpuzzled\b', r'\blost\b', r'\buncertain\b', r'\bunsure\b',
                    r'\bperplexed\b', r'\bmisunderstood\b', r'\bdon\'t understand\b', r'\bunclear\b', r'\bambiguous\b',
                    r'\bdisorientated\b', r'\bmixed up\b', r'\bmuddled\b', r'\bdon\'t get it\b', r'\bwhat\?\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\btotally\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.MOTIVATED: {
                'keywords': [
                    r'\bmotivated\b', r'\binspired\b', r'\bdetermined\b', r'\bdriven\b', r'\bfocused\b',
                    r'\bready\b', r'\beager\b', r'\bexcited\b', r'\benthusiastic\b', r'\bpassionate\b',
                    r'\bambitious\b', r'\bcommitted\b', r'\bdedicated\b', r'\bpumped\b', r'\benergized\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [r'\breally\b', r'\bvery\b', r'\bextremely\b', r'\bso\b', r'\bincredibly\b'],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: [r'\ba bit\b', r'\bslightly\b', r'\bsomewhat\b', r'\ba little\b']
                }
            },
            EmotionCategory.NEUTRAL: {
                'keywords': [
                    r'\bneutral\b', r'\bokay\b', r'\bfine\b', r'\balright\b', r'\baverage\b',
                    r'\bnormal\b', r'\bregular\b', r'\bstandard\b', r'\bordinary\b', r'\bcommon\b'
                ],
                'intensity_modifiers': {
                    EmotionIntensity.HIGH: [],
                    EmotionIntensity.MEDIUM: [],  # Default
                    EmotionIntensity.LOW: []
                }
            }
        }
        
        # Compile all patterns for faster matching
        for emotion, data in self.emotion_patterns.items():
            data['compiled_keywords'] = [re.compile(pattern, re.IGNORECASE) for pattern in data['keywords']]
            for intensity, modifiers in data['intensity_modifiers'].items():
                data['intensity_modifiers'][intensity] = [re.compile(pattern, re.IGNORECASE) for pattern in modifiers]
    
    def detect_emotion(self, text: str) -> Dict:
        """
        Detect emotions in text using all available methods
        
        Args:
            text: The text to analyze for emotions
            
        Returns:
            Dictionary with detected emotions and confidence scores
        """
        results = {
            'primary_emotion': EmotionCategory.NEUTRAL,
            'primary_intensity': EmotionIntensity.MEDIUM,
            'confidence': 0.5,  # Default medium confidence
            'all_emotions': {},
            'sentiment': {
                'polarity': 0,  # -1 to 1
                'subjectivity': 0  # 0 to 1
            },
            'method_used': 'rule_based'  # Default method
        }
        
        # Apply rule-based detection first (always available)
        rule_results = self._rule_based_detection(text)
        results.update(rule_results)
        
        # Apply TextBlob sentiment analysis if available
        if self.textblob_available:
            sentiment_results = self._textblob_analysis(text)
            results['sentiment'] = sentiment_results
            results['method_used'] = 'textblob'
            
            # Adjust confidence based on subjectivity
            if sentiment_results['subjectivity'] > 0.5:
                results['confidence'] = min(results['confidence'] + 0.2, 1.0)
        
        # Apply transformer model if available (highest priority)
        if self.transformer_available and self.emotion_classifier:
            try:
                transformer_results = self._transformer_analysis(text)
                if transformer_results:
                    results.update(transformer_results)
                    results['method_used'] = 'transformer'
            except Exception as e:
                self.logger.error(f"Error in transformer analysis: {e}")
        
        return results
    
    def _rule_based_detection(self, text: str) -> Dict:
        """
        Detect emotions using rule-based keyword matching
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with detected emotions
        """
        results = {
            'primary_emotion': EmotionCategory.NEUTRAL,
            'primary_intensity': EmotionIntensity.MEDIUM,
            'confidence': 0.5,
            'all_emotions': {}
        }
        
        # Check for each emotion
        for emotion, data in self.emotion_patterns.items():
            emotion_score = 0
            intensity = EmotionIntensity.MEDIUM  # Default intensity
            
            # Check for emotion keywords
            for pattern in data['compiled_keywords']:
                matches = pattern.findall(text.lower())
                emotion_score += len(matches) * 0.2  # Each match adds 0.2 to score
            
            # Check for intensity modifiers if we found the emotion
            if emotion_score > 0:
                # Check high intensity modifiers
                high_intensity_count = 0
                for pattern in data['intensity_modifiers'][EmotionIntensity.HIGH]:
                    high_intensity_count += len(pattern.findall(text.lower()))
                
                # Check low intensity modifiers
                low_intensity_count = 0
                for pattern in data['intensity_modifiers'][EmotionIntensity.LOW]:
                    low_intensity_count += len(pattern.findall(text.lower()))
                
                # Determine intensity based on modifiers
                if high_intensity_count > low_intensity_count:
                    intensity = EmotionIntensity.HIGH
                elif low_intensity_count > 0:
                    intensity = EmotionIntensity.LOW
                
                # Store emotion with its score
                results['all_emotions'][emotion] = {
                    'score': min(emotion_score, 1.0),  # Cap at 1.0
                    'intensity': intensity
                }
        
        # Determine primary emotion (highest score)
        if results['all_emotions']:
            primary_emotion = max(
                results['all_emotions'].items(), 
                key=lambda x: x[1]['score']
            )
            results['primary_emotion'] = primary_emotion[0]
            results['primary_intensity'] = primary_emotion[1]['intensity']
            results['confidence'] = primary_emotion[1]['score']
        
        return results
    
    def _textblob_analysis(self, text: str) -> Dict:
        """
        Analyze sentiment using TextBlob
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not self.textblob_available:
            return {'polarity': 0, 'subjectivity': 0}
        
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,  # -1 to 1
            'subjectivity': blob.sentiment.subjectivity  # 0 to 1
        }
    
    def _transformer_analysis(self, text: str) -> Optional[Dict]:
        """
        Analyze emotions using transformer model
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with emotion analysis results or None if failed
        """
        if not self.transformer_available or not self.emotion_classifier:
            return None
        
        try:
            # Get predictions from model
            predictions = self.emotion_classifier(text)[0]
            
            # Map model labels to our emotion categories
            emotion_mapping = {
                'joy': EmotionCategory.HAPPY,
                'happiness': EmotionCategory.HAPPY,
                'sadness': EmotionCategory.SAD,
                'anger': EmotionCategory.ANGRY,
                'fear': EmotionCategory.ANXIOUS,
                'surprise': EmotionCategory.CONFUSED,
                'disgust': EmotionCategory.ANGRY,
                'neutral': EmotionCategory.NEUTRAL,
                'worry': EmotionCategory.ANXIOUS,
                'love': EmotionCategory.HAPPY,
                'stress': EmotionCategory.STRESSED,
                'confusion': EmotionCategory.CONFUSED,
                'enthusiasm': EmotionCategory.MOTIVATED
            }
            
            # Process predictions
            all_emotions = {}
            for pred in predictions:
                label = pred['label'].lower()
                score = pred['score']
                
                # Map to our emotion categories
                if label in emotion_mapping:
                    mapped_emotion = emotion_mapping[label]
                    
                    # Determine intensity based on score
                    if score > 0.7:
                        intensity = EmotionIntensity.HIGH
                    elif score > 0.3:
                        intensity = EmotionIntensity.MEDIUM
                    else:
                        intensity = EmotionIntensity.LOW
                    
                    # Store or update emotion
                    if mapped_emotion in all_emotions:
                        if score > all_emotions[mapped_emotion]['score']:
                            all_emotions[mapped_emotion] = {
                                'score': score,
                                'intensity': intensity
                            }
                    else:
                        all_emotions[mapped_emotion] = {
                            'score': score,
                            'intensity': intensity
                        }
            
            # Determine primary emotion (highest score)
            if all_emotions:
                primary_emotion = max(
                    all_emotions.items(), 
                    key=lambda x: x[1]['score']
                )
                
                return {
                    'primary_emotion': primary_emotion[0],
                    'primary_intensity': primary_emotion[1]['intensity'],
                    'confidence': primary_emotion[1]['score'],
                    'all_emotions': all_emotions
                }
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error in transformer analysis: {e}")
            return None
    
    def get_response_for_emotion(self, emotion: EmotionCategory, intensity: EmotionIntensity) -> str:
        """
        Get an appropriate response template for a detected emotion
        
        Args:
            emotion: The detected emotion
            intensity: The intensity of the emotion
            
        Returns:
            A response template string
        """
        # Response templates for different emotions and intensities
        response_templates = {
            EmotionCategory.HAPPY: {
                EmotionIntensity.HIGH: [
                    "I'm so glad to hear you're feeling great! That positive energy is contagious. 😊",
                    "That's wonderful! I love seeing you this happy. What's bringing you so much joy?",
                    "Amazing! Your happiness is radiating through your words. Let's keep this momentum going!"
                ],
                EmotionIntensity.MEDIUM: [
                    "I'm happy to hear you're in good spirits! What's been going well for you?",
                    "That's nice to hear! A positive mindset can make such a difference.",
                    "I'm glad things are looking up for you. What's been making you feel good?"
                ],
                EmotionIntensity.LOW: [
                    "I sense a bit of positivity there. Even small moments of happiness are worth celebrating.",
                    "That's good to hear. Sometimes even a little happiness can brighten our perspective.",
                    "I'm glad there's something making you feel a bit better. Would you like to talk more about it?"
                ]
            },
            EmotionCategory.SAD: {
                EmotionIntensity.HIGH: [
                    "I'm really sorry you're feeling this way. It sounds incredibly difficult, and I'm here to listen. 💙",
                    "That sounds really hard. I wish I could give you a hug right now. Would it help to talk more about what's going on?",
                    "I can hear how much pain you're in, and I want you to know you don't have to face it alone. I'm here with you."
                ],
                EmotionIntensity.MEDIUM: [
                    "I'm sorry you're feeling down. Would sharing more about what's happening help?",
                    "That sounds tough. It's okay to feel sad sometimes, and I'm here to listen.",
                    "I hear the sadness in your words. Would you like to talk about what's on your mind?"
                ],
                EmotionIntensity.LOW: [
                    "I notice a hint of sadness there. Even small feelings are valid and worth acknowledging.",
                    "Sometimes we feel a little blue, and that's okay. Is there something specific on your mind?",
                    "I'm picking up on some sadness. Would you like to explore what might be causing it?"
                ]
            },
            EmotionCategory.ANGRY: {
                EmotionIntensity.HIGH: [
                    "I can tell you're really upset right now, and that's completely valid. Would it help to talk through what happened? 🧡",
                    "Your frustration comes through clearly, and it sounds justified. I'm here to listen without judgment.",
                    "That situation would make anyone angry. Would it help to explore what options you have now?"
                ],
                EmotionIntensity.MEDIUM: [
                    "I can sense your frustration. Would you like to talk more about what's bothering you?",
                    "That does sound annoying. It's natural to feel irritated by these things.",
                    "I understand why that would make you upset. How have you been handling it so far?"
                ],
                EmotionIntensity.LOW: [
                    "I notice a bit of irritation there. Even small annoyances can build up over time.",
                    "That does sound a little frustrating. Would you like to talk more about it?",
                    "I can understand why that might bother you. Is there anything that might help the situation?"
                ]
            },
            EmotionCategory.ANXIOUS: {
                EmotionIntensity.HIGH: [
                    "I can hear how anxious you're feeling right now. Let's take a moment to breathe together. What's the biggest worry on your mind? 💚",
                    "That sounds really overwhelming. Your feelings of anxiety are completely valid, and I'm here to help you navigate them.",
                    "When anxiety is this intense, it can feel all-consuming. Let's break down what's happening and take it one step at a time."
                ],
                EmotionIntensity.MEDIUM: [
                    "I can sense your worry. Would it help to talk through what's making you anxious?",
                    "Feeling anxious is natural when facing uncertainty. What's on your mind?",
                    "I understand that anxious feeling. Sometimes naming our specific worries can help reduce them."
                ],
                EmotionIntensity.LOW: [
                    "I notice a hint of worry there. Even small concerns deserve attention.",
                    "It sounds like there's something on your mind. Would you like to explore what's causing that slight anxiety?",
                    "A little bit of nervousness is completely normal. Is there something specific you're concerned about?"
                ]
            },
            EmotionCategory.STRESSED: {
                EmotionIntensity.HIGH: [
                    "It sounds like you're under immense pressure right now. Let's take a moment to identify what needs your immediate attention and what can wait. 💜",
                    "I can hear how overwhelmed you are. When everything feels too much, sometimes we need to step back and just focus on the next small step.",
                    "That level of stress sounds really difficult to manage. Let's think about what small things might help lighten your load right now."
                ],
                EmotionIntensity.MEDIUM: [
                    "I can tell you're feeling the pressure. What's contributing most to your stress right now?",
                    "Balancing everything can be really challenging. Which part feels most overwhelming?",
                    "That does sound stressful. Sometimes talking through our priorities can help manage the load."
                ],
                EmotionIntensity.LOW: [
                    "I sense you're feeling a bit pressured. Even low levels of stress can affect us over time.",
                    "Life can get busy sometimes. Is there anything specific adding to your plate right now?",
                    "I notice a bit of tension there. Would it help to talk about what's on your mind?"
                ]
            },
            EmotionCategory.CONFUSED: {
                EmotionIntensity.HIGH: [
                    "It sounds like you're really struggling to make sense of this situation. That's completely understandable. Let's try to untangle it together, one piece at a time. 💭",
                    "When everything feels this confusing, it can be overwhelming. Let's start with what you do know and work from there.",
                    "I can hear how disoriented you feel right now. Sometimes writing things down or talking them through can help bring clarity."
                ],
                EmotionIntensity.MEDIUM: [
                    "I understand your confusion. Would it help to break this down into smaller parts?",
                    "It can be frustrating when things don't make sense. Which part feels most unclear?",
                    "That does sound confusing. Sometimes talking it through can help bring clarity."
                ],
                EmotionIntensity.LOW: [
                    "I sense some uncertainty there. Would it help to explore what's causing the confusion?",
                    "Sometimes things aren't immediately clear, and that's okay. What part feels a bit fuzzy?",
                    "I notice you're not entirely sure about this. Would you like to talk it through?"
                ]
            },
            EmotionCategory.MOTIVATED: {
                EmotionIntensity.HIGH: [
                    "Your enthusiasm is incredible! I love seeing this energy and determination. What's your first step toward making this happen? 🌟",
                    "Wow, you're really fired up about this! That kind of passion is exactly what drives meaningful change and achievement.",
                    "I can feel your motivation radiating through your words! Let's channel this amazing energy into an actionable plan."
                ],
                EmotionIntensity.MEDIUM: [
                    "I can sense your motivation. What's inspiring you right now?",
                    "That sounds like a great goal. What steps are you thinking of taking?",
                    "I like your positive energy. Having direction and purpose is so valuable."
                ],
                EmotionIntensity.LOW: [
                    "I notice a spark of interest there. Even small motivation can lead to meaningful action.",
                    "That sounds like something you're curious about. Would you like to explore it further?",
                    "I sense some potential enthusiasm. Sometimes starting small can build momentum."
                ]
            },
            EmotionCategory.NEUTRAL: {
                EmotionIntensity.HIGH: [
                    "I appreciate your balanced perspective on this. What would you like to focus on today?",
                    "You seem to be taking things as they come. Is there anything specific you'd like to discuss?",
                    "Sometimes a neutral stance gives us space to consider different options. What's on your mind?"
                ],
                EmotionIntensity.MEDIUM: [
                    "What's been on your mind lately?",
                    "I'm here to chat about whatever you'd like. What's important to you right now?",
                    "How can I support you today?"
                ],
                EmotionIntensity.LOW: [
                    "What would you like to talk about today?",
                    "I'm here and ready to listen. What's on your mind?",
                    "Is there something specific you'd like to explore in our conversation?"
                ]
            }
        }
        
        # Get templates for the emotion and intensity
        templates = response_templates.get(
            emotion, 
            response_templates[EmotionCategory.NEUTRAL]
        ).get(
            intensity, 
            response_templates[EmotionCategory.NEUTRAL][EmotionIntensity.MEDIUM]
        )
        
        # Return a random template
        import random
        return random.choice(templates)
    
    def track_emotion_over_time(self, user_id: str, emotion_data: Dict) -> None:
        """
        Track user emotions over time (stub for database integration)
        
        Args:
            user_id: The user's ID
            emotion_data: The emotion data to track
        """
        # This would normally save to a database
        # For now, just log it
        self.logger.info(f"Tracked emotion for user {user_id}: {emotion_data['primary_emotion']} ({emotion_data['primary_intensity']})")
    
    def get_emotion_summary(self, user_id: str, time_period: str = "week") -> Dict:
        """
        Get a summary of user emotions over time (stub for database integration)
        
        Args:
            user_id: The user's ID
            time_period: The time period to summarize (day, week, month)
            
        Returns:
            Dictionary with emotion summary data
        """
        # This would normally query a database
        # For now, return mock data
        return {
            "primary_emotions": {
                EmotionCategory.HAPPY: 0.3,
                EmotionCategory.STRESSED: 0.4,
                EmotionCategory.ANXIOUS: 0.2,
                EmotionCategory.NEUTRAL: 0.1
            },
            "trend": "Your stress levels have decreased by 15% this week, while happiness has increased by 10%.",
            "insight": "You tend to feel most positive in the mornings and more stressed in the evenings."
        }

# Create a singleton instance for easy import
emotion_engine = EmotionEngine()