import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from config.security import get_current_user
from models.user import User
from models.learning import Portfolio, Project
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


class PortfolioUpdate(BaseModel):
    headline: Optional[str] = None
    about: Optional[str] = None
    skills: Optional[List[str]] = None
    social_links: Optional[dict] = None
    is_public: Optional[bool] = None


class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    technologies: List[str] = []
    demo_url: Optional[str] = ""
    github_url: Optional[str] = ""
    image_url: Optional[str] = ""
    security_score: float = 0.0


class PortfolioResponse(BaseModel):
    id: int
    headline: str
    about: str
    skills: list
    social_links: dict
    is_public: bool
    projects: list = []

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    technologies: list
    demo_url: str
    github_url: str
    image_url: str
    security_score: float
    created_at: datetime
    class Config:
        from_attributes = True


async def _get_or_create_portfolio(user_id: int, db: AsyncSession) -> Portfolio:
    result = await db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        portfolio = Portfolio(user_id=user_id)
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
    return portfolio


@router.get("/me")
async def get_my_portfolio(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await _get_or_create_portfolio(current_user.id, db)
    result = await db.execute(select(Project).where(Project.portfolio_id == portfolio.id))
    projects = result.scalars().all()
    return {
        "id": portfolio.id,
        "headline": portfolio.headline,
        "about": portfolio.about,
        "skills": json.loads(portfolio.skills) if portfolio.skills else [],
        "social_links": json.loads(portfolio.social_links) if portfolio.social_links else {},
        "is_public": portfolio.is_public,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "projects": [ProjectResponse.model_validate(p) for p in projects],
    }


@router.put("/me")
async def update_portfolio(
    data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await _get_or_create_portfolio(current_user.id, db)
    if data.headline is not None:
        portfolio.headline = data.headline
    if data.about is not None:
        portfolio.about = data.about
    if data.skills is not None:
        portfolio.skills = json.dumps(data.skills)
    if data.social_links is not None:
        portfolio.social_links = json.dumps(data.social_links)
    if data.is_public is not None:
        portfolio.is_public = data.is_public
    await db.commit()
    return {"status": "updated"}


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def add_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await _get_or_create_portfolio(current_user.id, db)
    project = Project(
        portfolio_id=portfolio.id,
        title=data.title,
        description=data.description or "",
        technologies=json.dumps(data.technologies),
        demo_url=data.demo_url or "",
        github_url=data.github_url or "",
        image_url=data.image_url or "",
        security_score=data.security_score,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    portfolio = await _get_or_create_portfolio(current_user.id, db)
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.portfolio_id == portfolio.id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
