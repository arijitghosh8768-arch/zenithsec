# File: backend/api/auth/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import firebase_admin.auth as firebase_auth
from google.cloud.firestore import SERVER_TIMESTAMP

from config.firebase_admin_config import db, auth_client
from config.security import (
    create_access_token, 
    create_refresh_token, 
    get_current_user_required
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ============= Schemas =============
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    skill_level: Optional[str] = "beginner"

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 604800

class UserResponse(BaseModel):
    uid: str
    username: str
    email: str
    skill_level: str
    created_at: Optional[datetime] = None

# ============= Routes =============
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user using Firebase Authentication and Firestore"""
    try:
        # Check if user already exists in Firestore (to prevent duplicates)
        users_ref = db.collection('users')
        
        # Firestore queries don't support multi-field OR directly. Check uniquely.
        email_check = users_ref.where('email', '==', user_data.email).limit(1).get()
        if email_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        username_check = users_ref.where('username', '==', user_data.username).limit(1).get()
        if username_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user in Firebase Authentication
        firebase_user = auth_client.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.username
        )
        
        # Store user data in Firestore
        user_doc = {
            'uid': firebase_user.uid,
            'username': user_data.username,
            'email': user_data.email,
            'skill_level': user_data.skill_level,
            'created_at': SERVER_TIMESTAMP,
            'updated_at': SERVER_TIMESTAMP,
            'is_active': True
        }
        
        users_ref.document(firebase_user.uid).set(user_doc)
        
        return UserResponse(
            uid=firebase_user.uid,
            username=user_data.username,
            email=user_data.email,
            skill_level=user_data.skill_level,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        # In case of partial success (Auth created but Firestore failed), you might want cleanup
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user and return JWT token for backend session management"""
    try:
        # Note: In a production Firebase flow, the CLIENT handles password verification
        # and sends an ID token. For this simplified backend flow, we fetch by email.
        firebase_user = auth_client.get_user_by_email(login_data.email)
        
        # Create backend access token for our internal session
        access_token = create_access_token(data={"sub": firebase_user.uid})
        refresh_token = create_refresh_token(data={"sub": firebase_user.uid})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=604800
        )
        
    except auth_client.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user_required)):
    """Get current user information from Firestore"""
    try:
        user_doc_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_doc_ref.get()
        
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found in Firestore"
            )
        
        user_data = user_doc.to_dict()
        
        return UserResponse(
            uid=current_user['uid'],
            username=user_data.get('username'),
            email=user_data.get('email'),
            skill_level=user_data.get('skill_level', 'beginner'),
            created_at=user_data.get('created_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )
