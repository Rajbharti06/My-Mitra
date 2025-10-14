#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test script to verify human-like response enhancements.
"""

import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.llm.human_like_response import make_human_like


def test_enhancements():
    """Test various enhancements to responses"""
    print("=== HUMAN-LIKE RESPONSE ENHANCEMENT TEST ===\n")
    
    # Test cases with different scenarios
    test_cases = [
        {
            "user_input": "what is the weather today",
            "response": "the weather is sunny with a chance of rain in the afternoon"
        },
        {
            "user_input": "i am feeling really sad today",
            "response": "i am sorry to hear that. would you like to talk about it"
        },
        {
            "user_input": "what is your favorite color",
            "response": "i do not have personal preferences, but i can help you with color choices"
        },
        {
            "user_input": "tell me a joke",
            "response": "why do not scientists trust atoms because they make up everything"
        },
        {
            "user_input": "i am so excited about my new job",
            "response": "that is wonderful news"
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases):
        user_input = test_case["user_input"]
        original_response = test_case["response"]
        enhanced_response = make_human_like(original_response, user_input)
        
        print(f"Test {i+1}:")
        print(f"  User Input: {user_input}")
        print(f"  Original:   {original_response}")
        print(f"  Enhanced:   {enhanced_response}")
        print("  " + "="*50 + "\n")
    
    print("=== TEST COMPLETE ===")


if __name__ == "__main__":
    test_enhancements()