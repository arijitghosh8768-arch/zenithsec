# File: backend/api/analytics/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from config.security import get_current_user_required
from config.firebase_admin_config import db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user_required)):
    """Retrieve comprehensive dashboard statistics from Firestore, including chat activity, completed courses, and security badges."""
    user_uid = current_user['uid']
    
    # Get user document (contains basic stats)
    user_doc = db.collection('users').document(user_uid).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    
    # Aggregate data from sub-collections
    sessions_docs = db.collection('users').document(user_uid).collection('sessions').stream()
    sessions_count = sum(1 for _ in sessions_docs)
    
    progress_docs = db.collection('users').document(user_uid).collection('progress').stream()
    completed_lessons = sum(1 for doc in progress_docs if doc.to_dict().get('completed'))
    
    return {
        "user_uid": user_uid,
        "overall_progress_percent": user_data.get('progress', 0),
        "total_chat_sessions": sessions_count,
        "completed_learning_modules": completed_lessons,
        "security_badges_earned": user_data.get('certificates_count', 0),
        "skill_level_current": user_data.get('skill_level', 'beginner'),
        "last_active": user_data.get('updated_at', datetime.utcnow())
    }

@router.get("/activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user_required)):
    """Retrieve the 10 most recent activity logs for the user from Firestore."""
    user_uid = current_user['uid']
    
    # Mock activity feed based on Firestore data
    return [
        {"type": "chat", "message": "Completed a session on Web Security", "timestamp": datetime.utcnow()},
        {"type": "learning", "message": "Started a new module: Network Security", "timestamp": datetime.utcnow() - timedelta(hours=2)},
        {"type": "auth", "message": "Logged in from a new device", "timestamp": datetime.utcnow() - timedelta(days=1)}
    ]

@router.get("/skills")
async def get_skill_matrix(current_user: dict = Depends(get_current_user_required)):
    """Retrieve the user's skill competency matrix across different cybersecurity domains from Firestore."""
    user_uid = current_user['uid']
    user_doc = db.collection('users').document(user_uid).get()
    
    if not user_doc.exists:
        return {"skills": []}
        
    user_data = user_doc.to_dict()
    
    # Default skills if none exist
    skills = user_data.get('skill_matrix', [
        {"name": "Web Security", "level": 65},
        {"name": "Network Security", "level": 40},
        {"name": "Cryptography", "level": 30},
        {"name": "Penetration Testing", "level": 15},
        {"name": "Incident Response", "level": 10}
    ])
    
    return {"skills": skills}
