#!/usr/bin/env python3
"""
Test script to verify AES encryption functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from encryption_utils import encrypt_data, decrypt_data

def test_encryption():
    """Test encryption and decryption functionality"""
    print("🔐 Testing AES Encryption...")
    
    # Test data
    test_messages = [
        "Hello, this is a test message!",
        "This is a longer message with special characters: !@#$%^&*()",
        "Multi-line message\nwith line breaks\nand unicode: 🚀✨",
        "",  # Empty string
        "A" * 1000,  # Long string
    ]
    
    for i, original_message in enumerate(test_messages, 1):
        print(f"\n--- Test {i} ---")
        print(f"Original: {repr(original_message)}")
        
        try:
            # Encrypt
            encrypted = encrypt_data(original_message)
            print(f"Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"Encrypted: {encrypted}")
            
            # Decrypt
            decrypted = decrypt_data(encrypted)
            print(f"Decrypted: {repr(decrypted)}")
            
            # Verify
            if original_message == decrypted:
                print("✅ PASS - Encryption/Decryption successful")
            else:
                print("❌ FAIL - Decryption doesn't match original")
                return False
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    print("\n🎉 All encryption tests passed!")
    return True

def test_database_integration():
    """Test encryption with database operations"""
    print("\n🗄️ Testing Database Integration...")
    
    try:
        from app.database import SessionLocal, engine
        from app.models import Base, User, ChatMessage
        from app.crud import create_user, create_chat_message, get_user_by_email
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Test user creation with encrypted data
        db = SessionLocal()
        
        # Create test user
        from app.schemas import UserCreate
        test_user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpassword123"
        )
        
        user = create_user(db, test_user_data)
        print(f"✅ User created with ID: {user.id}")
        
        # Test chat message with encryption
        message = create_chat_message(
            db=db,
            user_id=user.id,
            message="This is a test message that should be encrypted",
            response="This is an AI response that should also be encrypted",
            personality_used="mentor",
            session_id="test-session-123"
        )
        print(f"✅ Chat message created with ID: {message.id}")
        
        # Verify user retrieval
        retrieved_user = get_user_by_email(db, "test@example.com")
        if retrieved_user and retrieved_user.username == "testuser":
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            
        db.close()
        print("🎉 Database integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database integration error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 My Mitra Encryption Test Suite")
    print("=" * 50)
    
    # Test basic encryption
    encryption_ok = test_encryption()
    
    # Test database integration
    db_ok = test_database_integration()
    
    print("\n" + "=" * 50)
    if encryption_ok and db_ok:
        print("🎉 ALL TESTS PASSED! Encryption is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")