"""
Admin Dashboard Routes for My Mitra: Builder's Redemption
Provides secure admin interface for user management and encrypted message control.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from . import models, schemas, crud, security
from .database import get_db
from encryption_utils import decrypt_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_admin_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Verify admin token and return admin user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = security.verify_admin_token(token, credentials_exception)
        user = crud.get_user(db, username=token_data.username)
        if user is None or user.role != "admin":
            raise credentials_exception
        return user
    except Exception:
        raise credentials_exception

# Admin Dashboard Schemas
class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    preferred_personality: str
    created_at: datetime
    total_messages: int
    last_activity: Optional[datetime]

class AdminChatMessageResponse(BaseModel):
    id: int
    user_id: int
    username: str
    message_preview: str  # First 100 chars of decrypted message
    personality_used: str
    session_id: Optional[str]
    created_at: datetime

# Admin Routes

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get overall dashboard statistics"""
    total_users = db.query(models.User).count()
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    total_messages = db.query(models.ChatMessage).count()
    total_habits = db.query(models.Habit).count()
    total_journals = db.query(models.Journal).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_messages": total_messages,
        "total_habits": total_habits,
        "total_journals": total_journals,
        "admin_user": current_admin.username
    }

@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with their activity stats"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    user_responses = []
    for user in users:
        # Get message count and last activity
        message_count = db.query(models.ChatMessage).filter(models.ChatMessage.user_id == user.id).count()
        last_message = db.query(models.ChatMessage).filter(
            models.ChatMessage.user_id == user.id
        ).order_by(models.ChatMessage.created_at.desc()).first()
        
        user_responses.append(AdminUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            preferred_personality=user.preferred_personality,
            created_at=user.created_at,
            total_messages=message_count,
            last_activity=last_message.created_at if last_message else None
        ))
    
    return user_responses

@router.get("/messages")
async def list_messages(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List encrypted messages with preview (admin can see first 100 chars)"""
    query = db.query(models.ChatMessage).join(models.User)
    
    if user_id:
        query = query.filter(models.ChatMessage.user_id == user_id)
    
    messages = query.order_by(models.ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    message_responses = []
    for msg in messages:
        try:
            # Decrypt message for preview (admin privilege)
            decrypted_message = decrypt_data(msg.message_encrypted.decode())
            preview = decrypted_message[:100] + "..." if len(decrypted_message) > 100 else decrypted_message
            
            user = db.query(models.User).filter(models.User.id == msg.user_id).first()
            
            message_responses.append(AdminChatMessageResponse(
                id=msg.id,
                user_id=msg.user_id,
                username=user.username if user else "Unknown",
                message_preview=preview,
                personality_used=msg.personality_used,
                session_id=msg.session_id,
                created_at=msg.created_at
            ))
        except Exception as e:
            logger.error(f"Failed to decrypt message {msg.id}: {e}")
            message_responses.append(AdminChatMessageResponse(
                id=msg.id,
                user_id=msg.user_id,
                username="Unknown",
                message_preview="[Decryption Failed]",
                personality_used=msg.personality_used,
                session_id=msg.session_id,
                created_at=msg.created_at
            ))
    
    return message_responses

@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {user.username} {'activated' if user.is_active else 'deactivated'}"}

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a specific message (admin privilege)"""
    message = db.query(models.ChatMessage).filter(models.ChatMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    
    return {"message": f"Message {message_id} deleted successfully"}

@router.post("/create-admin")
async def create_admin_user(
    username: str,
    email: str,
    password: str,
    current_admin: models.User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new admin user (only existing admins can do this)"""
    # Check if user already exists
    existing_user = crud.get_user(db, username=username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create admin user
    admin_user_data = schemas.UserCreate(
        username=username,
        email=email,
        password=password
    )
    
    new_admin = crud.create_user(db, admin_user_data)
    new_admin.role = "admin"
    db.commit()
    
    return {"message": f"Admin user {username} created successfully"}