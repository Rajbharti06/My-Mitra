#!/usr/bin/env python3
"""
Test script to verify personality-based chat system
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_personalities():
    """Test all three personality types"""
    print("🎭 Testing Personality-Based Chat System")
    print("=" * 50)
    
    personalities = [
        {
            "type": "mentor",
            "test_message": "I'm feeling overwhelmed with my studies and don't know how to manage my time better.",
            "expected_traits": ["guidance", "wisdom", "structured advice"]
        },
        {
            "type": "motivator", 
            "test_message": "I've been procrastinating on my goals and feel like giving up.",
            "expected_traits": ["encouragement", "energy", "positive reinforcement"]
        },
        {
            "type": "coach",
            "test_message": "I want to build better habits but I keep failing to stick to them.",
            "expected_traits": ["actionable steps", "accountability", "practical strategies"]
        }
    ]
    
    for i, personality in enumerate(personalities, 1):
        print(f"\n--- Test {i}: {personality['type'].upper()} Personality ---")
        print(f"Test Message: {personality['test_message']}")
        
        try:
            # Test chat with specific personality
            response = requests.post(
                f"{BASE_URL}/chat/",
                json={
                    "message": personality['test_message'],
                    "personality": personality['type']
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get('response', '')
                personality_used = data.get('personality_used', '')
                
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Personality Used: {personality_used}")
                print(f"✅ Response Length: {len(ai_response)} characters")
                print(f"📝 AI Response: {ai_response[:200]}...")
                
                # Check if response seems appropriate for personality
                response_lower = ai_response.lower()
                personality_indicators = {
                    "mentor": ["guidance", "experience", "wisdom", "suggest", "recommend", "consider"],
                    "motivator": ["you can", "believe", "achieve", "motivation", "energy", "excited", "amazing"],
                    "coach": ["step", "action", "plan", "strategy", "goal", "habit", "practice", "implement"]
                }
                
                indicators_found = []
                for indicator in personality_indicators.get(personality['type'], []):
                    if indicator in response_lower:
                        indicators_found.append(indicator)
                
                if indicators_found:
                    print(f"✅ Personality Indicators Found: {', '.join(indicators_found)}")
                else:
                    print("⚠️  No clear personality indicators found")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
        
        # Small delay between requests
        time.sleep(2)

def test_personality_switching():
    """Test switching between personalities"""
    print(f"\n🔄 Testing Personality Switching")
    print("-" * 30)
    
    try:
        # Test switching to coach
        response = requests.post(
            f"{BASE_URL}/chat/personality",
            json={"personality": "coach"}
        )
        
        if response.status_code == 200:
            print("✅ Successfully switched to coach personality")
        else:
            print(f"❌ Failed to switch personality: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Personality switching error: {e}")

def test_available_personalities():
    """Test getting available personalities"""
    print(f"\n📋 Testing Available Personalities Endpoint")
    print("-" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/chat/personalities")
        
        if response.status_code == 200:
            personalities = response.json()
            print("✅ Available personalities:")
            for personality in personalities:
                print(f"  - {personality['type']}: {personality['name']}")
                print(f"    Description: {personality['description']}")
        else:
            print(f"❌ Failed to get personalities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting personalities: {e}")

def test_health_check():
    """Test health check endpoint"""
    print(f"\n🏥 Testing Health Check")
    print("-" * 20)
    
    try:
        response = requests.get("http://localhost:8000/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed")
            print(f"  Status: {health_data.get('status')}")
            print(f"  Ollama: {health_data.get('ollama_status')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🧪 My Mitra Personality System Test Suite")
    print("=" * 60)
    
    # Test health first
    test_health_check()
    
    # Test available personalities
    test_available_personalities()
    
    # Test personality switching
    test_personality_switching()
    
    # Test all personalities
    test_personalities()
    
    print("\n" + "=" * 60)
    print("🎉 Personality testing complete!")
    print("Check the responses above to verify personality characteristics.")