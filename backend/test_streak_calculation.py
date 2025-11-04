#!/usr/bin/env python3
"""
Test script to validate streak calculation logic for different habit frequencies.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models, crud, schemas
import tempfile

def create_test_db():
    """Create a temporary test database."""
    db_file = tempfile.mktemp(suffix='.db')
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), db_file

def test_daily_habit_streak():
    """Test streak calculation for daily habits."""
    print("Testing daily habit streak calculation...")
    
    db, db_file = create_test_db()
    
    try:
        # Create a test user
        user = models.User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="dummy"
        )
        db.add(user)
        db.commit()
        
        # Create a daily habit
        habit_data = schemas.HabitCreate(
            title="Daily Exercise",
            description="Exercise every day",
            frequency="daily"
        )
        
        habit = crud.create_habit(db, user_id=1, habit=habit_data)
        print(f"Created habit: {habit['title']} (ID: {habit['id']})")
        
        # Test first completion
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"First completion - Streak: {result.streak_count}")
        assert result.streak_count == 1, f"Expected streak 1, got {result.streak_count}"
        
        # Simulate completing the next day
        habit_obj = db.query(models.Habit).filter(models.Habit.id == habit['id']).first()
        habit_obj.last_completed = datetime.now() - timedelta(days=1)
        db.commit()
        
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"Next day completion - Streak: {result.streak_count}")
        assert result.streak_count == 2, f"Expected streak 2, got {result.streak_count}"
        
        # Simulate missing a day (2 days gap)
        habit_obj.last_completed = datetime.now() - timedelta(days=2)
        db.commit()
        
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"After missing a day - Streak: {result.streak_count}")
        assert result.streak_count == 1, f"Expected streak 1 (reset), got {result.streak_count}"
        
        print("✅ Daily habit streak test passed!")
        
    finally:
        db.close()
        os.unlink(db_file)

def test_weekly_habit_streak():
    """Test streak calculation for weekly habits."""
    print("\nTesting weekly habit streak calculation...")
    
    db, db_file = create_test_db()
    
    try:
        # Create a test user
        user = models.User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="dummy"
        )
        db.add(user)
        db.commit()
        
        # Create a weekly habit
        habit_data = schemas.HabitCreate(
            title="Weekly Review",
            description="Review goals weekly",
            frequency="weekly"
        )
        
        habit = crud.create_habit(db, user_id=1, habit=habit_data)
        print(f"Created habit: {habit['title']} (ID: {habit['id']})")
        
        # Test first completion
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"First completion - Streak: {result.streak_count}")
        assert result.streak_count == 1, f"Expected streak 1, got {result.streak_count}"
        
        # Simulate completing the next week
        habit_obj = db.query(models.Habit).filter(models.Habit.id == habit['id']).first()
        habit_obj.last_completed = datetime.now() - timedelta(weeks=1)
        db.commit()
        
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"Next week completion - Streak: {result.streak_count}")
        assert result.streak_count == 2, f"Expected streak 2, got {result.streak_count}"
        
        # Simulate missing a week (2 weeks gap)
        habit_obj.last_completed = datetime.now() - timedelta(weeks=2)
        db.commit()
        
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"After missing a week - Streak: {result.streak_count}")
        assert result.streak_count == 1, f"Expected streak 1 (reset), got {result.streak_count}"
        
        print("✅ Weekly habit streak test passed!")
        
    finally:
        db.close()
        os.unlink(db_file)

def test_monthly_habit_streak():
    """Test streak calculation for monthly habits."""
    print("\nTesting monthly habit streak calculation...")
    
    db, db_file = create_test_db()
    
    try:
        # Create a test user
        user = models.User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="dummy"
        )
        db.add(user)
        db.commit()
        
        # Create a monthly habit
        habit_data = schemas.HabitCreate(
            title="Monthly Budget Review",
            description="Review budget monthly",
            frequency="monthly"
        )
        
        habit = crud.create_habit(db, user_id=1, habit=habit_data)
        print(f"Created habit: {habit['title']} (ID: {habit['id']})")
        
        # Test first completion
        result = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"First completion - Streak: {result.streak_count}")
        assert result.streak_count == 1, f"Expected streak 1, got {result.streak_count}"
        
        print("✅ Monthly habit streak test passed!")
        
    finally:
        db.close()
        os.unlink(db_file)

def test_duplicate_completion_prevention():
    """Test that habits cannot be completed multiple times in the same period."""
    print("\nTesting duplicate completion prevention...")
    
    db, db_file = create_test_db()
    
    try:
        # Create a test user
        user = models.User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="dummy"
        )
        db.add(user)
        db.commit()
        
        # Create a daily habit
        habit_data = schemas.HabitCreate(
            title="Daily Reading",
            description="Read every day",
            frequency="daily"
        )
        
        habit = crud.create_habit(db, user_id=1, habit=habit_data)
        
        # Complete the habit
        result1 = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"First completion - Streak: {result1.streak_count}")
        
        # Try to complete again on the same day
        result2 = crud.complete_habit(db, user_id=1, habit_id=habit['id'])
        print(f"Second completion attempt - Streak: {result2.streak_count}")
        
        # Should return the same habit without incrementing streak
        assert result1.streak_count == result2.streak_count, "Streak should not increment for duplicate completion"
        
        print("✅ Duplicate completion prevention test passed!")
        
    finally:
        db.close()
        os.unlink(db_file)

if __name__ == "__main__":
    print("🧪 Running streak calculation tests...\n")
    
    try:
        test_daily_habit_streak()
        test_weekly_habit_streak()
        test_monthly_habit_streak()
        test_duplicate_completion_prevention()
        
        print("\n🎉 All streak calculation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)