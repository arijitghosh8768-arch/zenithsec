# File: backend/api/learning_hub/routes.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from config.security import get_current_user_required
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from config.firebase_admin_config import db

router = APIRouter(prefix="/api/learning", tags=["Learning Hub"])

class CourseResponse(BaseModel):
    id: str  # Changed to str for Firestore IDs
    course_id: str
    title: str
    description: str
    category: str
    difficulty: str
    duration_hours: int
    lessons_count: int

class LessonResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    content: str
    order: int
    duration_minutes: int

class ProgressUpdate(BaseModel):
    course_id: str
    lesson_id: str
    completed: bool = True
    score: float = 0.0
    time_spent: int = 0

class ProgressResponse(BaseModel):
    course_id: str
    lesson_id: str
    completed: bool
    score: float
    time_spent: int
    completed_at: Optional[datetime] = None

# Static data (In production, these would move to Firestore 'courses' collection)
SEED_COURSES = [
    {"id": "1", "course_id": "web-sec-101", "title": "Web Application Security Fundamentals", "description": "Master OWASP Top 10 vulnerabilities, XSS, SQL injection, CSRF, and learn to build secure web applications.", "category": "Web Security", "difficulty": "beginner", "duration_hours": 8, "lessons_count": 12},
    {"id": "2", "course_id": "net-sec-101", "title": "Network Security Essentials", "description": "Learn firewalls, IDS/IPS, VPN protocols, network scanning, and traffic analysis with hands-on labs.", "category": "Network Security", "difficulty": "beginner", "duration_hours": 10, "lessons_count": 15},
    {"id": "3", "course_id": "crypto-201", "title": "Applied Cryptography", "description": "Deep dive into encryption algorithms, PKI, digital signatures, and implementing secure communication.", "category": "Cryptography", "difficulty": "intermediate", "duration_hours": 12, "lessons_count": 10},
    {"id": "4", "course_id": "pentest-301", "title": "Advanced Penetration Testing", "description": "Master recon, exploitation, post-exploitation, and professional penetration testing methodology.", "category": "Penetration Testing", "difficulty": "advanced", "duration_hours": 20, "lessons_count": 18},
]

@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(current_user: dict = Depends(get_current_user_required)):
    """List available courses (using seed data for now)"""
    return [CourseResponse(**c) for c in SEED_COURSES]

@router.get("/courses/{course_id}")
async def get_course(course_id: str, current_user: dict = Depends(get_current_user_required)):
    """Get specific course details"""
    course = next((c for c in SEED_COURSES if c["course_id"] == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Stub lessons for now
    lessons = [
        {"id": "l1", "lesson_id": f"{course_id}-1", "title": "Introduction", "content": "Welcome to the course...", "order": 1, "duration_minutes": 15}
    ]
    
    return {
        "course": course,
        "lessons": lessons
    }

@router.post("/progress")
async def update_progress(data: ProgressUpdate, current_user: dict = Depends(get_current_user_required)):
    """Update user progress in Firestore"""
    user_uid = current_user['uid']
    progress_ref = db.collection('users').document(user_uid).collection('progress').document(f"{data.course_id}_{data.lesson_id}")
    
    from google.cloud.firestore import SERVER_TIMESTAMP
    progress_data = data.model_dump()
    progress_data['updated_at'] = SERVER_TIMESTAMP
    if data.completed:
        progress_data['completed_at'] = SERVER_TIMESTAMP
        
    progress_ref.set(progress_data, merge=True)
    return {"status": "ok"}

@router.get("/progress", response_model=List[ProgressResponse])
async def get_progress(current_user: dict = Depends(get_current_user_required)):
    """Get user progress from Firestore"""
    user_uid = current_user['uid']
    docs = db.collection('users').document(user_uid).collection('progress').stream()
    
    results = []
    for doc in docs:
        results.append(ProgressResponse(**doc.to_dict()))
    return results
