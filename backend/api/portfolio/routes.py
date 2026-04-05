# File: backend/api/portfolio/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from config.security import get_current_user_required
from config.firebase_admin_config import db

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

class ProjectBase(BaseModel):
    title: str
    description: str
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    technologies: List[str] = []

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime

class PortfolioResponse(BaseModel):
    user_uid: str
    username: str
    bio: Optional[str] = None
    skills: List[str] = []
    projects: List[ProjectResponse] = []
    certificates_count: int = 0

@router.get("/me", response_model=PortfolioResponse)
async def get_my_portfolio(current_user: dict = Depends(get_current_user_required)):
    """Retrieve the current user's portfolio and associated projects from Firestore"""
    user_uid = current_user['uid']
    user_doc = db.collection('users').document(user_uid).get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_data = user_doc.to_dict()
    
    # Get projects from sub-collection
    projects_docs = db.collection('users').document(user_uid).collection('projects').stream()
    projects = []
    for doc in projects_docs:
        p_data = doc.to_dict()
        p_data['id'] = doc.id
        projects.append(ProjectResponse(**p_data))
        
    return PortfolioResponse(
        user_uid=user_uid,
        username=user_data.get('username', 'Anonymous'),
        bio=user_data.get('bio', 'Security Researcher'),
        skills=user_data.get('skills', ['Cybersecurity']),
        projects=projects,
        certificates_count=user_data.get('certificates_count', 0)
    )

@router.post("/projects", response_model=ProjectResponse)
async def add_project(data: ProjectCreate, current_user: dict = Depends(get_current_user_required)):
    """Add a new project to the user's Firestore portfolio"""
    user_uid = current_user['uid']
    project_ref = db.collection('users').document(user_uid).collection('projects').document()
    
    project_data = data.model_dump()
    project_data['created_at'] = datetime.utcnow()
    project_ref.set(project_data)
    
    project_data['id'] = project_ref.id
    return ProjectResponse(**project_data)

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user_required)):
    """Delete a specific project from the user's Firestore portfolio"""
    user_uid = current_user['uid']
    db.collection('users').document(user_uid).collection('projects').document(project_id).delete()
    return {"status": "deleted"}
