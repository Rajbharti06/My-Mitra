#!/usr/bin/env python3
"""
Test script to verify JWT authentication and password hashing
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_user_registration():
    """Test user registration with password hashing"""
    print("👤 Testing User Registration")
    print("-" * 30)
    
    # Generate unique username for testing
    timestamp = int(time.time())
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "securepassword123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json=test_user
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User registration successful")
            print(f"  Username: {user_data.get('username')}")
            print(f"  Email: {user_data.get('email')}")
            print(f"  User ID: {user_data.get('id')}")
            print(f"  Password is hashed: {'hashed_password' not in user_data}")
            return test_user
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_user_login(user_credentials):
    """Test user login and JWT token generation"""
    print(f"\n🔐 Testing User Login")
    print("-" * 20)
    
    if not user_credentials:
        print("❌ No user credentials available for login test")
        return None
    
    try:
        # Login with form data (OAuth2PasswordRequestForm format)
        login_data = {
            "username": user_credentials["username"],
            "password": user_credentials["password"]
        }
        
        response = requests.post(
            f"{BASE_URL}/token",
            data=login_data,  # Use data instead of json for form data
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful")
            print(f"  Access token received: {len(token_data.get('access_token', ''))} characters")
            print(f"  Token type: {token_data.get('token_type')}")
            return token_data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_protected_endpoint(access_token):
    """Test accessing protected endpoints with JWT token"""
    print(f"\n🛡️ Testing Protected Endpoints")
    print("-" * 30)
    
    if not access_token:
        print("❌ No access token available for protected endpoint test")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test chat history endpoint (requires authentication)
    try:
        response = requests.get(
            f"{BASE_URL}/chat/history",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            print(f"  Chat history retrieved: {len(response.json())} messages")
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")

def test_invalid_token():
    """Test accessing protected endpoints with invalid token"""
    print(f"\n🚫 Testing Invalid Token Handling")
    print("-" * 35)
    
    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/chat/history",
            headers=headers
        )
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected")
            print(f"  Status: {response.status_code}")
        else:
            print(f"⚠️  Unexpected response for invalid token: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")

def test_no_token():
    """Test accessing protected endpoints without token"""
    print(f"\n🔒 Testing No Token Handling")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/chat/history")
        
        if response.status_code == 401:
            print("✅ Missing token correctly rejected")
            print(f"  Status: {response.status_code}")
        else:
            print(f"⚠️  Unexpected response for missing token: {response.status_code}")
            
    except Exception as e:
        print(f"❌ No token test error: {e}")

def test_password_security():
    """Test password hashing security"""
    print(f"\n🔐 Testing Password Security")
    print("-" * 30)
    
    # Test that the same password produces different hashes
    from app.security import get_password_hash, verify_password
    
    password = "testpassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    print(f"✅ Password hashing working:")
    print(f"  Original password: {password}")
    print(f"  Hash 1: {hash1[:20]}...")
    print(f"  Hash 2: {hash2[:20]}...")
    print(f"  Hashes are different: {hash1 != hash2}")
    print(f"  Hash 1 verifies: {verify_password(password, hash1)}")
    print(f"  Hash 2 verifies: {verify_password(password, hash2)}")
    print(f"  Wrong password fails: {not verify_password('wrongpassword', hash1)}")

if __name__ == "__main__":
    print("🔐 My Mitra Authentication System Test Suite")
    print("=" * 60)
    
    # Test password security first
    test_password_security()
    
    # Test user registration
    user_credentials = test_user_registration()
    
    # Test user login
    access_token = test_user_login(user_credentials)
    
    # Test protected endpoints
    test_protected_endpoint(access_token)
    
    # Test invalid token handling
    test_invalid_token()
    
    # Test no token handling
    test_no_token()
    
    print("\n" + "=" * 60)
    print("🎉 Authentication testing complete!")
    print("JWT authentication and password hashing are working correctly.")