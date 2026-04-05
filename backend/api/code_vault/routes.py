# File: backend/api/code_vault/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from config.security import get_current_user_required
from config.firebase_admin_config import db

router = APIRouter(prefix="/api/codevault", tags=["Code Vault"])

class RepoBase(BaseModel):
    name: str
    description: Optional[str] = None
    language: str
    is_public: bool = False

class RepoCreate(RepoBase):
    pass

class RepoResponse(RepoBase):
    id: str
    created_at: datetime
    updated_at: datetime
    owner_uid: str

class FileResponse(BaseModel):
    id: str
    filename: str
    content: str
    language: str
    created_at: datetime

@router.get("/repos", response_model=List[RepoResponse])
async def list_repos(current_user: dict = Depends(get_current_user_required)):
    """List all code repositories for the user from Firestore"""
    user_uid = current_user['uid']
    repos_docs = db.collection('users').document(user_uid).collection('code_repos').stream()
    
    results = []
    for doc in repos_docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(RepoResponse(**data))
        
    return results

@router.post("/repos", response_model=RepoResponse)
async def create_repo(data: RepoCreate, current_user: dict = Depends(get_current_user_required)):
    """Create a new repository in Firestore for the user's code vault"""
    user_uid = current_user['uid']
    repo_ref = db.collection('users').document(user_uid).collection('code_repos').document()
    
    repo_data = data.model_dump()
    repo_data['owner_uid'] = user_uid
    repo_data['created_at'] = datetime.utcnow()
    repo_data['updated_at'] = datetime.utcnow()
    
    repo_ref.set(repo_data)
    
    repo_data['id'] = repo_ref.id
    return RepoResponse(**repo_data)

@router.get("/repos/{repo_id}/files", response_model=List[FileResponse])
async def list_files(repo_id: str, current_user: dict = Depends(get_current_user_required)):
    """Retrieve all files associated with a specific code vault repository from Firestore"""
    user_uid = current_user['uid']
    files_docs = db.collection('users').document(user_uid).collection('code_repos').document(repo_id).collection('files').stream()
    
    results = []
    for doc in files_docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(FileResponse(**data))
        
    return results

@router.post("/repos/{repo_id}/files")
async def add_file(repo_id: str, filename: str, content: str, language: str, current_user: dict = Depends(get_current_user_required)):
    """Add a new file to a specific code vault repository in Firestore"""
    user_uid = current_user['uid']
    file_ref = db.collection('users').document(user_uid).collection('code_repos').document(repo_id).collection('files').document()
    
    file_data = {
        "filename": filename,
        "content": content,
        "language": language,
        "created_at": datetime.utcnow()
    }
    
    file_ref.set(file_data)
    
    # Update repository modified date
    db.collection('users').document(user_uid).collection('code_repos').document(repo_id).update({
        "updated_at": datetime.utcnow()
    })
    
    return {"status": "ok", "file_id": file_ref.id}
