import random
import re
import random
from typing import Optional, List, Dict

class HumanLikeResponseEnhancer:
    """Enhances AI responses to sound more natural and human-like"""
    
    def __init__(self):
        # Common conversational fillers - expanded list
        self.fillers = [
            "Hmm", "Oh", "Ah", "Well", "You know", "Actually",
            "Hmm, let's see", "Oh right", "So", "You know what I mean?",
            "Wait a second", "Believe it or not", "I was thinking",
            "Funny you should mention that", "To be honest", "You see"
        ]
        
        # Emotional response patterns based on user input
        self.emotional_patterns = {
            r'\bstress\b|\banxious\b|\bworried\b': {
                'responses': [
                    "I can sense that weight you're carrying… it sounds really tough.",
                    "That sounds so stressful. I'm here to listen if you want to share more.",
                    "Stress can feel so overwhelming, but I'm glad you're opening up about it."
                ],
                'followups': [
                    "What do you think is making this feel so heavy right now?",
                    "Is there a specific part of this that feels the most challenging?",
                    "Would it help to talk through what's been on your mind?"
                ]
            },
            r'\bhappy\b|\bexcited\b|\bjoy\b|\bgreat\b': {
                'responses': [
                    "Oh that's wonderful to hear! You sound really excited about this.",
                    "I love seeing you this happy – tell me more about what's making you feel this way!",
                    "Your joy is contagious! What's been the best part of it for you?"
                ],
                'followups': [
                    "How long have you been feeling like this? It's great!",
                    "What do you think is the most exciting part about this?",
                    "Is there someone you want to share this happiness with?"
                ]
            },
            r'\bsad\b|\bupset\b|\bhurt\b|\bdisappointed\b': {
                'responses': [
                    "I'm so sorry you're feeling this way. It must be really hard.",
                    "That sounds really painful. I'm here for you, even if it's just to listen.",
                    "Heartache can feel so heavy, but you're not going through this alone."
                ],
                'followups': [
                    "Do you want to talk about what happened? Sometimes sharing helps.",
                    "What do you think might help you feel even a little better right now?",
                    "Is there something you wish could be different about this situation?"
                ]
            },
            r'\bconfused\b|\buncertain\b|\bnot sure\b': {
                'responses': [
                    "It's completely normal to feel confused sometimes – especially with complex situations.",
                    "Uncertainty can be really uncomfortable, but it also means there are possibilities.",
                    "I get that feeling of not knowing which way to turn. Let's try to untangle this together."
                ],
                'followups': [
                    "What's the first thing that comes to mind when you think about this?",
                    "Is there a small part of this that feels clearer than the rest?",
                    "If you had all the answers right now, what would you want them to be?"
                ]
            },
            r'\bthank\b|\bappreciate\b': {
                'responses': [
                    "You're welcome – it means a lot that I can be here for you.",
                    "I'm just glad I could help in some way.",
                    "Anytime! That's what friends are for, right?"
                ],
                'followups': [
                    "How are you feeling now after our chat?",
                    "Is there anything else on your mind you'd like to talk about?",
                    "I'm here whenever you need to talk again."
                ]
            }
        }
        
        # Common human-like expressions - expanded list
        self.expressions = [
            "you know?", "right?", "you see", "I get that", "makes sense",
            "it's like", "sort of", "kind of", "maybe", "perhaps",
            "I think", "I feel like", "to be honest", "frankly", "truthfully",
            "if that makes sense", "you know what I mean", "in my experience",
            "from what I've seen", "I've noticed that", "to tell you the truth"
        ]
        
        # Punctuation variations to make text flow more naturally
        self.punctuation_variants = {
            ".": [".", "...", ", you know?", ", maybe?", ", if that makes sense", ".  ", ". "],
            "?": ["?", "? Hmm", "? What do you think?", "? I'm curious"],
            "!": ["!", "! That's amazing!", "! How cool is that?", "! Wow"]
        }
        
        # Common contractions to make text more conversational
        self.contractions = {
            "i am": "i'm",
            "you are": "you're",
            "he is": "he's",
            "she is": "she's",
            "it is": "it's",
            "we are": "we're",
            "they are": "they're",
            "i have": "i've",
            "you have": "you've",
            "we have": "we've",
            "they have": "they've",
            "i will": "i'll",
            "you will": "you'll",
            "we will": "we'll",
            "they will": "they'll",
            "do not": "don't",
            "does not": "doesn't",
            "did not": "didn't",
            "cannot": "can't",
            "could not": "couldn't",
            "would not": "wouldn't",
            "should not": "shouldn't",
            "is not": "isn't",
            "are not": "aren't",
            "have not": "haven't",
            "has not": "hasn't"
        }
    
    def detect_emotional_context(self, user_input: str) -> Optional[Dict]:
        """Detect emotional context from user input"""
        user_input_lower = user_input.lower()
        for pattern, emotional_data in self.emotional_patterns.items():
            if re.search(pattern, user_input_lower):
                return emotional_data
        return None
    
    def add_conversational_filler(self, response: str) -> str:
        """Add natural conversational fillers to make the response flow better"""
        # Don't add filler if response is very short or already has one
        if len(response.split()) < 5:
            return response
        
        if any(filler.lower() in response.lower() for filler in self.fillers[:5]):
            return response
        
        # Add a filler at the beginning with some probability
        if random.random() < 0.3:
            filler = random.choice(self.fillers)
            # Capitalize the response if we're adding a filler
            return f"{filler}, {response[0].lower() + response[1:]}" if response[0].isupper() else f"{filler}, {response}"
        
        return response
    
    def vary_punctuation(self, response: str) -> str:
        """Vary punctuation to make the response feel more natural"""
        if not response or len(response) < 2:
            return response
        
        # Process the end punctuation
        last_char = response[-1]
        if last_char in self.punctuation_variants and random.random() < 0.4:
            variants = self.punctuation_variants[last_char]
            new_punctuation = random.choice(variants)
            return response[:-1] + new_punctuation
        
        return response
    
    def add_expressions(self, response: str) -> str:
        """Add human-like expressions to make the response more relatable"""
        words = response.split()
        if len(words) < 8:
            return response
        
        # Determine positions where we could insert an expression
        possible_positions = []
        for i, word in enumerate(words):
            # Don't insert after the first word or before the last word
            if i > 0 and i < len(words) - 1:
                # Check if the previous word ends with punctuation
                if words[i-1][-1] in ['.', ',', '!', '?']:
                    possible_positions.append(i)
        
        if possible_positions and random.random() < 0.3:
            position = random.choice(possible_positions)
            expression = random.choice(self.expressions)
            # Add comma if needed
            if words[position-1][-1] not in ['.', ',', '!', '?']:
                words[position-1] += ','
            # Insert the expression
            words.insert(position, expression)
            return ' '.join(words)
        
        return response
    
    def add_follow_up_question(self, response: str, emotional_data: Optional[Dict] = None) -> str:
        """Add a natural follow-up question to keep the conversation going"""
        # Don't add a follow-up if the response is already a question or very long
        if '?' in response or len(response.split()) > 30:
            return response
        
        # Helper to ensure clean sentence boundary before appending follow-up
        def _ensure_sentence_end(text: str) -> str:
            base = text.rstrip()
            if not base:
                return base
            # Replace trailing mid-sentence punctuation with a period
            if base[-1] in [',', ';', ':']:
                base = base[:-1]
            # Ensure it ends with terminal punctuation
            if base[-1] not in ['.', '!', '?']:
                base = base + '.'
            return base
        
        # Use emotional-specific follow-ups if available
        if emotional_data and 'followups' in emotional_data and random.random() < 0.5:
            followup = random.choice(emotional_data['followups'])
            base = _ensure_sentence_end(response)
            return f"{base} {followup}"
        
        # Generic follow-ups
        generic_followups = [
            "What do you think about that?",
            "How does that make you feel?",
            "Want to share more about it?",
            "Does that resonate with you at all?"
        ]
        
        if random.random() < 0.3:
            followup = random.choice(generic_followups)
            base = _ensure_sentence_end(response)
            return f"{base} {followup}"
        
        return response
    
    def use_contractions(self, response: str) -> str:
        """Convert full forms to contractions to make text more conversational"""
        if not response: return response
        
        # Create a copy to work with
        result = response
        
        # Handle each contraction individually to ensure proper case handling
        for full_form, contraction in self.contractions.items():
            # Get the different case versions of the full form
            full_lower = full_form.lower()
            full_title = full_form.title()
            full_upper = full_form.upper()
            
            # Create appropriate replacements
            replacement_lower = contraction
            replacement_title = contraction[0].upper() + contraction[1:]
            replacement_upper = contraction.upper()
            
            # Special handling for "I am" since it's common and important
            if full_lower == "i am":
                # Handle all variations of "I am"
                result = result.replace("I am", "I'm").replace("i am", "i'm").replace("I AM", "I'M")
                continue
            
            # For other contractions, handle all case variations
            # First check for exact matches with different cases
            result = result.replace(full_title, replacement_title)
            result = result.replace(full_lower, replacement_lower)
            result = result.replace(full_upper, replacement_upper)
            
            # Also check for capitalized first word with lowercase second (common in sentences)
            if len(full_lower.split()) == 2:
                first_word, second_word = full_lower.split()
                capitalized_version = first_word.capitalize() + " " + second_word
                capitalized_replacement = replacement_title
                result = result.replace(capitalized_version, capitalized_replacement)
        
        return result
    
    def enhance(self, response: str, user_input: str) -> str:
        """Main method to enhance a response to be more human-like"""
        if not response:
            return "I'm here to listen. What's on your mind?"
        
        # Make sure response starts with capital letter
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        
        # Detect emotional context
        emotional_data = self.detect_emotional_context(user_input)
        
        # Apply enhancements in sequence
        enhanced = self.use_contractions(response)  # Use contractions first for more natural flow
        
        # Increase probability of punctuation variations
        if random.random() < 0.8:
            enhanced = self.vary_punctuation(enhanced)
        
        # Increase probability of conversational filler
        if random.random() < 0.7:
            enhanced = self.add_conversational_filler(enhanced)
        
        # Increase probability of expressions
        if random.random() < 0.7:
            enhanced = self.add_expressions(enhanced)
        
        # Add follow-up question with higher probability
        if random.random() < 0.6:
            enhanced = self.add_follow_up_question(enhanced, emotional_data)
        
        # Add natural hesitation with higher probability
        if random.random() < 0.3 and len(enhanced.split()) > 5:
            words = enhanced.split()
            hesitation_pos = random.randint(1, len(words) - 2)
            hesitation = random.choice(["um", "uh", "like", "you know"])
            words.insert(hesitation_pos, hesitation)
            enhanced = ' '.join(words)
        
        # Keep very large responses reasonable without cutting normal replies
        # Only trim if the response is extremely long (e.g., > 400 words)
        if len(enhanced.split()) > 400:
            words = enhanced.split()
            enhanced = ' '.join(words[:380]) + '...'
        
        # Clean up any double spaces or weird formatting that might have been introduced
        enhanced = ' '.join(enhanced.split())
        
        return enhanced
    
    def get_emotionally_adapted_response(self, user_input: str) -> Optional[str]:
        """Get an emotionally adapted response based on user input"""
        emotional_data = self.detect_emotional_context(user_input)
        if emotional_data and 'responses' in emotional_data:
            return random.choice(emotional_data['responses'])
        return None

# Create a singleton instance for easy import
enhancer = HumanLikeResponseEnhancer()

# Helper function for quick access
def make_human_like(response: str, user_input: str) -> str:
    """Quick helper to make a response more human-like"""
    return enhancer.enhance(response, user_input)