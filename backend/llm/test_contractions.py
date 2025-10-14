#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script specifically for testing the contractions functionality.
"""

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.llm.human_like_response import HumanLikeResponseEnhancer


def test_contractions():
    """Test the contractions functionality with various cases"""
    print("=== CONTRACTIONS TEST ===\n")
    
    enhancer = HumanLikeResponseEnhancer()
    
    # Test cases specifically designed to test contractions
    test_cases = [
        "i am happy to help you",
        "you are doing a great job",
        "i have been thinking about this",
        "we will meet tomorrow",
        "do not worry about it",
        "I AM EXCITED",
        "You are the best",
        "They have arrived"
    ]
    
    # Run tests
    for i, test_text in enumerate(test_cases):
        contracted_text = enhancer.use_contractions(test_text)
        
        print(f"Test {i+1}:")
        print(f"  Original:  {test_text}")
        print(f"  Contracted: {contracted_text}")
        print("  " + "="*50 + "\n")
    
    # Also test the full enhance method
    print("=== FULL ENHANCE TEST WITH CONTRACTIONS ===\n")
    
    full_test_cases = [
        {
            "user_input": "how are you",
            "response": "i am doing well, thank you"
        },
        {
            "user_input": "what have you been up to",
            "response": "i have been working on some new features"
        }
    ]
    
    for i, test_case in enumerate(full_test_cases):
        user_input = test_case["user_input"]
        original_response = test_case["response"]
        enhanced_response = enhancer.enhance(original_response, user_input)
        
        print(f"Full Test {i+1}:")
        print(f"  User Input: {user_input}")
        print(f"  Original:   {original_response}")
        print(f"  Enhanced:   {enhanced_response}")
        print("  " + "="*50 + "\n")
    
    print("=== TEST COMPLETE ===")


if __name__ == "__main__":
    test_contractions()