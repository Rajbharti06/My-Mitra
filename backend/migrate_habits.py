from sqlalchemy import create_engine, Column, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database configuration
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base, Habit

def run_migration():
    print("Starting migration to add 'archived' field to Habit table...")
    
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Check if the archived column already exists
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(habits)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'archived' not in columns:
            print("Adding 'archived' column to habits table...")
            conn.execute(text("ALTER TABLE habits ADD COLUMN archived BOOLEAN DEFAULT 0"))
            conn.commit()
            print("Column 'archived' added successfully!")
        else:
            print("Column 'archived' already exists!")
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()