import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from config.security import get_current_user
from models.user import User
from models.learning import Course, Lesson, LearningProgress
from typing import List
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/learning", tags=["Learning Hub"])


class CourseResponse(BaseModel):
    id: int
    course_id: str
    title: str
    description: str
    category: str
    difficulty: str
    duration_hours: int
    lessons_count: int
    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    id: int
    lesson_id: str
    title: str
    content: str
    order: int
    duration_minutes: int
    class Config:
        from_attributes = True


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
    class Config:
        from_attributes = True


# Seed data for courses
SEED_COURSES = [
    {"course_id": "web-sec-101", "title": "Web Application Security Fundamentals", "description": "Master OWASP Top 10 vulnerabilities, XSS, SQL injection, CSRF, and learn to build secure web applications.", "category": "Web Security", "difficulty": "beginner", "duration_hours": 8, "lessons_count": 12},
    {"course_id": "net-sec-101", "title": "Network Security Essentials", "description": "Learn firewalls, IDS/IPS, VPN protocols, network scanning, and traffic analysis with hands-on labs.", "category": "Network Security", "difficulty": "beginner", "duration_hours": 10, "lessons_count": 15},
    {"course_id": "crypto-201", "title": "Applied Cryptography", "description": "Deep dive into encryption algorithms, PKI, digital signatures, and implementing secure communication.", "category": "Cryptography", "difficulty": "intermediate", "duration_hours": 12, "lessons_count": 10},
    {"course_id": "pentest-301", "title": "Advanced Penetration Testing", "description": "Master recon, exploitation, post-exploitation, and professional penetration testing methodology.", "category": "Penetration Testing", "difficulty": "advanced", "duration_hours": 20, "lessons_count": 18},
    {"course_id": "malware-201", "title": "Malware Analysis & Reverse Engineering", "description": "Static and dynamic analysis, debugging, disassembly, and understanding malware behavior.", "category": "Malware Analysis", "difficulty": "intermediate", "duration_hours": 15, "lessons_count": 14},
    {"course_id": "cloud-sec-201", "title": "Cloud Security (AWS/Azure/GCP)", "description": "Secure cloud architectures, IAM, container security, and cloud-native security tools.", "category": "Cloud Security", "difficulty": "intermediate", "duration_hours": 12, "lessons_count": 11},
    {"course_id": "forensics-101", "title": "Digital Forensics Fundamentals", "description": "Evidence collection, disk forensics, memory analysis, and incident response procedures.", "category": "Digital Forensics", "difficulty": "beginner", "duration_hours": 10, "lessons_count": 12},
    {"course_id": "secure-code-101", "title": "Secure Coding Practices", "description": "Input validation, authentication patterns, authorization models, and secure development lifecycle.", "category": "Secure Development", "difficulty": "beginner", "duration_hours": 8, "lessons_count": 10},
]


@router.get("/courses", response_model=List[CourseResponse])
async def list_courses(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    if not courses:
        # Seed courses on first access
        for c in SEED_COURSES:
            course = Course(**c)
            db.add(course)
        await db.commit()
        result = await db.execute(select(Course))
        courses = result.scalars().all()
    return courses


@router.get("/courses/{course_id}")
async def get_course(course_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(select(Lesson).where(Lesson.course_id == course.id).order_by(Lesson.order))
    lessons = result.scalars().all()

    return {
        "course": CourseResponse.model_validate(course),
        "lessons": [LessonResponse.model_validate(l) for l in lessons]
    }


@router.post("/progress")
async def update_progress(
    data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.course_id == data.course_id,
            LearningProgress.lesson_id == data.lesson_id
        )
    )
    progress = result.scalar_one_or_none()
    if progress:
        progress.completed = data.completed
        progress.score = data.score
        progress.time_spent += data.time_spent
        if data.completed:
            from datetime import datetime, timezone
            progress.completed_at = datetime.now(timezone.utc)
    else:
        progress = LearningProgress(
            user_id=current_user.id,
            course_id=data.course_id,
            lesson_id=data.lesson_id,
            completed=data.completed,
            score=data.score,
            time_spent=data.time_spent,
        )
        if data.completed:
            from datetime import datetime, timezone
            progress.completed_at = datetime.now(timezone.utc)
        db.add(progress)

    await db.commit()
    return {"status": "ok"}


@router.get("/progress", response_model=List[ProgressResponse])
async def get_progress(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LearningProgress).where(LearningProgress.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/recommendations")
async def get_recommendations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get AI-powered learning recommendations based on progress."""
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.completed == True
        )
    )
    completed = result.scalars().all()
    completed_courses = {p.course_id for p in completed}

    recommendations = []
    for course in SEED_COURSES:
        if course["course_id"] not in completed_courses:
            if current_user.skill_level == "beginner" and course["difficulty"] == "beginner":
                recommendations.append(course)
            elif current_user.skill_level == "intermediate" and course["difficulty"] in ("beginner", "intermediate"):
                recommendations.append(course)
            elif current_user.skill_level == "advanced":
                recommendations.append(course)

    return {"recommendations": recommendations[:5]}
