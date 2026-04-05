# File: backend/config/security.py

from datetime import datetime, timedelta
from typing import Optional, Union, Dict
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from config.settings import settings
from config.firebase_admin_config import auth_client

# Password hashing (kept for legacy support or local check)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Security scheme
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a backend JWT access token for Firebase UIDs"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None

async def get_current_user_required(
    token: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from JWT token - raises exception if not authenticated"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token.credentials, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        user_uid: str = payload.get("sub")
        if user_uid is None:
            raise credentials_exception
            
        # Verify user exists in Firebase Auth
        try:
            firebase_user = auth_client.get_user(user_uid)
            return {
                "uid": user_uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name
            }
        except Exception:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

async def get_current_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Get current user from JWT token (returns None if not authenticated)"""
    if token is None:
        return None
    
    try:
        payload = jwt.decode(
            token.credentials, 
            settings.SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        user_uid: str = payload.get("sub")
        if user_uid is None:
            return None
            
        # Optional: Verify with Firebase
        try:
            firebase_user = auth_client.get_user(user_uid)
            return {
                "uid": user_uid,
                "email": firebase_user.email,
                "display_name": firebase_user.display_name
            }
        except Exception:
            return None
            
    except JWTError:
        return None

async def get_current_user_ws(
    websocket: WebSocket
) -> Optional[dict]:
    """Get current user from WebSocket connection using token query param"""
    try:
        token = websocket.query_params.get("token")
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            user_uid: str = payload.get("sub")
            if user_uid is None:
                return None
            
            # Verify with Firebase
            firebase_user = auth_client.get_user(user_uid)
            return {"uid": user_uid, "email": firebase_user.email}
                
        except (JWTError, Exception):
            return None
            
    except Exception:
        return None

# Keep these for compatibility if needed, but they are no longer used for core auth
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
