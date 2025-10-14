from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./mymitra.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_last_messages(user_id: str, limit: int = 8):
    """
    Returns the last N messages for a user.
    NOTE: This is a stub. It returns a fixed list of messages.
    """
    # In a real implementation, this would query the database
    # and decrypt the messages.
    return [
        {"role": "user", "text": "I'm tired today."},
        {"role": "mitra", "text": "I’m sorry — that sounds rough. 😞 Do you want a quick 5-minute breathing exercise or would you prefer to talk about what made you tired?"}
    ]

def save_message(user_id: str, role: str, text: str):
    """
    Saves a message to the database.
    NOTE: This is a stub. It doesn't do anything yet.
    """
    # In a real implementation, this would encrypt the message
    # and save it to the database.
    pass

