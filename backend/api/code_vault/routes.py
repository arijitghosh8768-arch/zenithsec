import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from config.database import get_db
from config.security import get_current_user
from models.user import User
from models.repository import Repository, File, Commit
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/code", tags=["Code Vault"])


class RepoCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    visibility: str = "private"
    language: Optional[str] = ""


class RepoResponse(BaseModel):
    id: int
    repo_id: str
    name: str
    description: str
    visibility: str
    language: str
    stars: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class FileCreate(BaseModel):
    path: str
    content: str = ""


class FileResponse(BaseModel):
    id: int
    path: str
    content: str
    file_hash: str
    size: int
    created_at: datetime
    class Config:
        from_attributes = True


class CommitResponse(BaseModel):
    id: int
    message: str
    commit_hash: str
    author: str
    files_changed: int
    created_at: datetime
    class Config:
        from_attributes = True


class CodeScanResult(BaseModel):
    vulnerabilities: List[dict] = []
    secrets: List[dict] = []
    quality_issues: List[dict] = []
    score: float = 100.0


@router.get("/repos", response_model=List[RepoResponse])
async def list_repos(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id).order_by(desc(Repository.updated_at))
    )
    return result.scalars().all()


@router.post("/repos", response_model=RepoResponse, status_code=status.HTTP_201_CREATED)
async def create_repo(data: RepoCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = Repository(
        repo_id=str(uuid.uuid4())[:8],
        user_id=current_user.id,
        name=data.name,
        description=data.description or "",
        visibility=data.visibility,
        language=data.language or "",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    return repo


@router.get("/repos/{repo_id}", response_model=RepoResponse)
async def get_repo(repo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/repos/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(repo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await db.delete(repo)
    await db.commit()


@router.get("/repos/{repo_id}/files", response_model=List[FileResponse])
async def list_files(repo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    result = await db.execute(select(File).where(File.repository_id == repo.id))
    return result.scalars().all()


@router.post("/repos/{repo_id}/files", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file(
    repo_id: str, data: FileCreate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    file = File(
        repository_id=repo.id,
        path=data.path,
        content=data.content,
        file_hash=hashlib.sha256(data.content.encode()).hexdigest(),
        size=len(data.content.encode()),
    )
    db.add(file)

    # Auto-commit
    commit = Commit(
        repository_id=repo.id,
        message=f"Add {data.path}",
        commit_hash=hashlib.sha256(f"{data.path}{data.content}".encode()).hexdigest()[:12],
        author=current_user.username,
        files_changed=1,
    )
    db.add(commit)
    await db.commit()
    await db.refresh(file)
    return file


@router.post("/repos/{repo_id}/scan", response_model=CodeScanResult)
async def scan_repo(repo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await db.execute(select(File).where(File.repository_id == repo.id))
    files = result.scalars().all()

    vulns = []
    secrets = []
    quality = []
    score = 100.0

    for f in files:
        content = f.content.lower()
        # Vulnerability checks
        if "eval(" in content:
            vulns.append({"file": f.path, "line": 0, "type": "code_injection", "detail": "Use of eval() - potential code injection", "severity": "high"})
            score -= 10
        if "exec(" in content:
            vulns.append({"file": f.path, "line": 0, "type": "code_injection", "detail": "Use of exec() - potential code injection", "severity": "high"})
            score -= 10
        if "password" in content and "=" in content:
            secrets.append({"file": f.path, "type": "hardcoded_password", "detail": "Possible hardcoded password detected"})
            score -= 15
        if "api_key" in content or "apikey" in content:
            secrets.append({"file": f.path, "type": "api_key", "detail": "Possible API key in source code"})
            score -= 15
        if "todo" in content or "fixme" in content:
            quality.append({"file": f.path, "type": "todo", "detail": "TODO/FIXME found"})
            score -= 2

    return CodeScanResult(vulnerabilities=vulns, secrets=secrets, quality_issues=quality, score=max(score, 0))


@router.get("/repos/{repo_id}/commits", response_model=List[CommitResponse])
async def list_commits(repo_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Repository).where(Repository.repo_id == repo_id, Repository.user_id == current_user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    result = await db.execute(
        select(Commit).where(Commit.repository_id == repo.id).order_by(desc(Commit.created_at))
    )
    return result.scalars().all()
