from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from config.database import get_db
from config.security import get_current_user
from models.user import User
from models.repository import Repository, Commit
from models.certificate import Certificate
from models.learning import LearningProgress, ChatSession, ChatMessage
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Repos count
    result = await db.execute(select(func.count(Repository.id)).where(Repository.user_id == current_user.id))
    repos_count = result.scalar() or 0

    # Certs count
    result = await db.execute(select(func.count(Certificate.id)).where(Certificate.user_id == current_user.id))
    certs_count = result.scalar() or 0

    # Completed lessons
    result = await db.execute(
        select(func.count(LearningProgress.id)).where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.completed == True
        )
    )
    completed_lessons = result.scalar() or 0

    # Chat sessions count
    result = await db.execute(select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id))
    chat_sessions = result.scalar() or 0

    # Calculate streak (days with activity in last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(func.count(func.distinct(func.date(LearningProgress.created_at))))
        .where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.created_at >= thirty_days_ago
        )
    )
    streak = result.scalar() or 0

    # Security score (based on activity)
    security_score = min(100, (completed_lessons * 5) + (repos_count * 10) + (certs_count * 15))

    return {
        "stats": {
            "repositories": repos_count,
            "certificates": certs_count,
            "completed_lessons": completed_lessons,
            "chat_sessions": chat_sessions,
            "streak_days": streak,
            "security_score": security_score,
        },
        "user": {
            "username": current_user.username,
            "skill_level": current_user.skill_level,
            "member_since": current_user.created_at.isoformat() if current_user.created_at else "",
        }
    }


@router.get("/activity")
async def get_activity(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get activity data for heatmap (last 365 days)."""
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    # Learning activity
    result = await db.execute(
        select(LearningProgress.created_at)
        .where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.created_at >= one_year_ago
        )
    )
    activity_dates = result.scalars().all()

    # Chat activity
    result = await db.execute(
        select(ChatMessage.created_at)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(
            ChatSession.user_id == current_user.id,
            ChatMessage.created_at >= one_year_ago
        )
    )
    chat_dates = result.scalars().all()

    # Commits
    result = await db.execute(
        select(Commit.created_at)
        .join(Repository, Commit.repository_id == Repository.id)
        .where(
            Repository.user_id == current_user.id,
            Commit.created_at >= one_year_ago
        )
    )
    commit_dates = result.scalars().all()

    # Aggregate by date
    activity_map = {}
    for dt in activity_dates + chat_dates + commit_dates:
        if dt:
            date_str = dt.strftime("%Y-%m-%d")
            activity_map[date_str] = activity_map.get(date_str, 0) + 1

    return {"activity": activity_map}


@router.get("/skills")
async def get_skills(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get skill progression data for radar chart."""
    # Derive skills from completed courses
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.user_id == current_user.id,
            LearningProgress.completed == True
        )
    )
    completed = result.scalars().all()

    skills = {
        "Web Security": 0,
        "Network Security": 0,
        "Cryptography": 0,
        "Penetration Testing": 0,
        "Malware Analysis": 0,
        "Cloud Security": 0,
        "Digital Forensics": 0,
        "Secure Coding": 0,
    }

    course_skill_map = {
        "web-sec-101": "Web Security",
        "net-sec-101": "Network Security",
        "crypto-201": "Cryptography",
        "pentest-301": "Penetration Testing",
        "malware-201": "Malware Analysis",
        "cloud-sec-201": "Cloud Security",
        "forensics-101": "Digital Forensics",
        "secure-code-101": "Secure Coding",
    }

    for p in completed:
        skill = course_skill_map.get(p.course_id)
        if skill:
            skills[skill] = min(100, skills[skill] + 20)

    return {"skills": skills}
