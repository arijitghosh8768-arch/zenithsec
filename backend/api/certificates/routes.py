import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import get_db
from config.security import get_current_user
from models.user import User
from models.certificate import Certificate, Verification
from api.certificates.blockchain import blockchain
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


class CertificateIssue(BaseModel):
    title: str
    description: Optional[str] = ""
    course_name: Optional[str] = ""


class CertificateResponse(BaseModel):
    id: int
    cert_id: str
    title: str
    description: str
    course_name: str
    blockchain_hash: str
    block_index: int
    issued_at: datetime
    is_verified: bool
    class Config:
        from_attributes = True


class VerifyResponse(BaseModel):
    is_valid: bool
    certificate: Optional[CertificateResponse] = None
    blockchain_verified: bool = False
    message: str = ""


@router.post("/issue", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def issue_certificate(
    data: CertificateIssue,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cert_id = f"ZSEC-{uuid.uuid4().hex[:8].upper()}"

    # Add to blockchain
    block = blockchain.add_certificate({
        "cert_id": cert_id,
        "user_id": current_user.id,
        "username": current_user.username,
        "title": data.title,
        "course_name": data.course_name or "",
    })

    cert = Certificate(
        cert_id=cert_id,
        user_id=current_user.id,
        title=data.title,
        description=data.description or "",
        course_name=data.course_name or "",
        blockchain_hash=block.hash,
        block_index=block.index,
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


@router.get("/mine", response_model=List[CertificateResponse])
async def get_my_certificates(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Certificate).where(Certificate.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{cert_id}", response_model=CertificateResponse)
async def get_certificate(cert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Certificate).where(Certificate.cert_id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert


@router.post("/verify", response_model=VerifyResponse)
async def verify_certificate_by_id(data: dict, db: AsyncSession = Depends(get_db)):
    cert_id = data.get("cert_id", "")
    result = await db.execute(select(Certificate).where(Certificate.cert_id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        return VerifyResponse(is_valid=False, message="Certificate not found")

    blockchain_valid = blockchain.verify_certificate(cert.block_index)

    # Record verification
    verification = Verification(certificate_id=cert.id, is_valid=blockchain_valid)
    db.add(verification)
    await db.commit()

    return VerifyResponse(
        is_valid=True,
        certificate=CertificateResponse.model_validate(cert),
        blockchain_verified=blockchain_valid,
        message="Certificate is valid and blockchain-verified" if blockchain_valid else "Certificate found but blockchain verification failed"
    )
