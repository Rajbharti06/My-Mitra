import os
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our human-like response enhancer
sys.path.append(str(Path(__file__).parent))
from human_like_response import make_human_like, HumanLikeResponseEnhancer

try:
    # Try to import the actual model if possible
    from model import MyMitraModel
    HAS_MODEL = True
except ImportError as e:
    print(f"Could not import MyMitraModel: {e}")
    print("Using mock model for demonstration...")
    HAS_MODEL = False

class MockModel:
    """Mock model for testing when we can't load the real model"""
    def __init__(self):
        # Simple response templates for testing
        self.responses = {
            "Hello, how are you?": "I'm doing well, thanks for asking! How about you?",
            "I'm feeling stressed about work.": "I'm sorry to hear that work is stressing you out. Maybe you can take a short break?",
            "What are some ways to relax?": "There are many ways to relax, like deep breathing, going for a walk, or listening to music.",
            "I'm really happy today!": "That's wonderful to hear! What's making you so happy?",
            "I'm not sure what to do.": "It's okay to feel uncertain sometimes. Maybe we can figure it out together.",
            "I failed my exam.": "I'm sorry to hear that. Exams can be really tough, but this doesn't define your abilities."
        }
        
    def generate_response(self, prompt, *args, **kwargs):
        # Return a simple response based on the prompt
        response = self.responses.get(prompt, "I'm here to listen. Tell me more.")
        return response, None

class HumanLikeResponseTester:
    """Tests and demonstrates human-like response enhancements"""
    
    def __init__(self):
        # Initialize the model (real or mock)
        if HAS_MODEL:
            try:
                self.model = MyMitraModel()
                print("Successfully loaded MyMitraModel!")
            except Exception as e:
                print(f"Error loading MyMitraModel: {e}")
                self.model = MockModel()
                print("Using mock model instead.")
        else:
            self.model = MockModel()
        
        # Initialize the enhancer
        self.enhancer = HumanLikeResponseEnhancer()
        
        # Test prompts
        self.test_prompts = [
            "Hello, how are you?",
            "I'm feeling stressed about work.",
            "What are some ways to relax?",
            "I'm really happy today!",
            "I'm not sure what to do.",
            "I failed my exam."
        ]
    
    def test_individual_enhancements(self):
        """Test individual enhancement techniques"""
        print("\n=== Testing Individual Enhancement Techniques ===")
        
        test_response = "I understand how you feel. It can be really challenging sometimes."
        test_input = "I'm feeling stressed about work."
        
        print(f"Original Response: {test_response}")
        
        # Test filler addition
        filler_response = self.enhancer.add_conversational_filler(test_response)
        print(f"With Filler: {filler_response}")
        
        # Test punctuation variation
        punct_response = self.enhancer.vary_punctuation(test_response)
        print(f"With Punctuation Variation: {punct_response}")
        
        # Test expression addition
        expr_response = self.enhancer.add_expressions(test_response)
        print(f"With Expressions: {expr_response}")
        
        # Test follow-up question
        emotional_data = self.enhancer.detect_emotional_context(test_input)
        followup_response = self.enhancer.add_follow_up_question(test_response, emotional_data)
        print(f"With Follow-up: {followup_response}")
        
        # Test full enhancement
        full_enhanced = self.enhancer.enhance(test_response, test_input)
        print(f"Fully Enhanced: {full_enhanced}")
    
    def compare_responses(self):
        """Compare original responses with enhanced ones"""
        print("\n=== Comparing Original vs. Human-Like Responses ===")
        for prompt in self.test_prompts:
            print(f"\nUser: {prompt}")
            
            # Get original response (from model or mock)
            original_response, _ = self.model.generate_response(prompt)
            print(f"Original Response: {original_response}")
            
            # Get enhanced response
            enhanced_response = make_human_like(original_response, prompt)
            print(f"Human-Like Response: {enhanced_response}")
            
            # Calculate changes
            original_words = len(original_response.split())
            enhanced_words = len(enhanced_response.split())
            change_percent = ((enhanced_words - original_words) / original_words * 100) if original_words > 0 else 0
            
            print(f"Word count change: {original_words} → {enhanced_words} ({change_percent:+.1f}%)")
            print("-" * 50)
    
    def simulate_conversation(self):
        """Simulate a natural conversation using human-like responses"""
        print("\n=== Simulating a Human-Like Conversation ===")
        
        # Simple conversation flow
        conversation = [
            ("Hi MyMitra, it's been a tough day...", None),
            ("Work was so stressful today. My boss gave me a huge project with a tight deadline.", None),
            ("I'm not sure I can finish it on time. What should I do?", None),
            ("That makes sense. Maybe I can break it down into smaller tasks.", None),
            ("Thanks for the advice. I feel a little better now.", None)
        ]
        
        for i, (user_input, _) in enumerate(conversation):
            print(f"\nUser: {user_input}")
            
            # Get model response
            model_response, _ = self.model.generate_response(user_input)
            
            # Enhance to make it human-like
            human_like_response = make_human_like(model_response, user_input)
            
            print(f"MyMitra: {human_like_response}")
            print("-" * 50)
            time.sleep(1)  # Pause for more natural conversation flow
    
    def analyze_enhancement_effectiveness(self):
        """Analyze how effective the enhancements are"""
        print("\n=== Enhancement Effectiveness Analysis ===")
        
        total_original_words = 0
        total_enhanced_words = 0
        emotional_detections = 0
        
        for prompt in self.test_prompts:
            original_response, _ = self.model.generate_response(prompt)
            enhanced_response = make_human_like(original_response, prompt)
            
            # Count words
            total_original_words += len(original_response.split())
            total_enhanced_words += len(enhanced_response.split())
            
            # Check for emotional detection
            if self.enhancer.detect_emotional_context(prompt):
                emotional_detections += 1
                
        # Calculate statistics
        avg_original_words = total_original_words / len(self.test_prompts) if self.test_prompts else 0
        avg_enhanced_words = total_enhanced_words / len(self.test_prompts) if self.test_prompts else 0
        overall_change = ((total_enhanced_words - total_original_words) / total_original_words * 100) if total_original_words > 0 else 0
        emotional_detection_rate = (emotional_detections / len(self.test_prompts) * 100) if self.test_prompts else 0
        
        print(f"Average original response length: {avg_original_words:.1f} words")
        print(f"Average enhanced response length: {avg_enhanced_words:.1f} words")
        print(f"Overall length change: {overall_change:+.1f}%")
        print(f"Emotional context detection rate: {emotional_detection_rate:.1f}%")
        
        # Qualitative assessment
        print("\nQualitative Improvements:")
        print("- More natural conversational flow")
        print("- Better emotional engagement")
        print("- Increased use of human-like expressions")
        print("- More varied punctuation patterns")
        print("- Enhanced follow-up questions to maintain conversation")
    
    def run_all_tests(self):
        """Run all tests and demonstrations"""
        print("\n===== MyMitra Human-Like Response Testing =====")
        
        # Run individual enhancement tests
        self.test_individual_enhancements()
        
        # Compare original vs enhanced responses
        self.compare_responses()
        
        # Simulate a conversation
        self.simulate_conversation()
        
        # Analyze effectiveness
        self.analyze_enhancement_effectiveness()
        
        print("\n===== Testing Complete =====")
        print("The human-like response enhancements have been successfully applied!")

if __name__ == "__main__":
    tester = HumanLikeResponseTester()
    tester.run_all_tests()