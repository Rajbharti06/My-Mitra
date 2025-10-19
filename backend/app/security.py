import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from . import schemas
from typing import Optional
from enum import Enum

load_dotenv() # Load environment variables from .env file

# User Roles for Admin Dashboard
class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("SECRET_KEY", "your-fallback-secret-key") # Fallback for local dev if .env not loaded
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ADMIN_TOKEN_EXPIRE_MINUTES = 60  # Longer session for admin dashboard

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# JWT Token
def create_access_token(data: dict, expires_delta: timedelta | None = None, is_admin: bool = False):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Use longer expiry for admin tokens
        minutes = ADMIN_TOKEN_EXPIRE_MINUTES if is_admin else ACCESS_TOKEN_EXPIRE_MINUTES
        expire = datetime.utcnow() + timedelta(minutes=minutes)
    
    to_encode.update({"exp": expire})
    # Add role information to token
    if is_admin:
        to_encode.update({"role": UserRole.ADMIN.value})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", UserRole.USER.value)
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    return token_data

def verify_admin_token(token: str, credentials_exception):
    """Verify token and ensure user has admin privileges"""
    token_data = verify_token(token, credentials_exception)
    if token_data.role != UserRole.ADMIN.value:
        raise credentials_exception
    return token_data

def create_admin_access_token(username: str, expires_delta: timedelta | None = None):
    """Create an admin access token with elevated privileges"""
    data = {"sub": username, "role": UserRole.ADMIN.value}
    return create_access_token(data, expires_delta, is_admin=True)
