# File: backend/api/certificates/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from config.security import get_current_user_required
from config.firebase_admin_config import db

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])

class CertificateResponse(BaseModel):
    id: str
    course_id: str
    course_name: str
    issue_date: datetime
    verification_hash: str
    user_uid: str
    user_name: str

class VerifyRequest(BaseModel):
    verification_hash: str

@router.get("/me", response_model=List[CertificateResponse])
async def list_my_certificates(current_user: dict = Depends(get_current_user_required)):
    """List all cybersecurity certificates earned by the user from Firestore"""
    user_uid = current_user['uid']
    certs_docs = db.collection('users').document(user_uid).collection('certificates').stream()
    
    results = []
    for doc in certs_docs:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(CertificateResponse(**data))
        
    return results

@router.post("/verify")
async def verify_certificate(data: VerifyRequest):
    """Verify the authenticity of a certificate using its cryptographic hash across the global Firestore index"""
    # Cross-user query for verification hashes
    global_certs = db.collection_group('certificates').where('verification_hash', '==', data.verification_hash).limit(1).stream()
    
    cert = next(global_certs, None)
    if not cert:
        raise HTTPException(status_code=404, detail="Invalid verification hash")
        
    return {
        "status": "valid",
        "certificate": cert.to_dict()
    }

@router.post("/generate/{course_id}")
async def generate_certificate(course_id: str, current_user: dict = Depends(get_current_user_required)):
    """Generate a new certificate in Firestore after successful course completion"""
    user_uid = current_user['uid']
    import hashlib
    import time
    
    # Generate a unique hash for verification
    verification_hash = hashlib.sha256(f"{user_uid}_{course_id}_{time.time()}".encode()).hexdigest()
    
    cert_data = {
        "course_id": course_id,
        "course_name": f"Mastery in {course_id.replace('-', ' ').title()}",
        "issue_date": datetime.utcnow(),
        "verification_hash": verification_hash,
        "user_uid": user_uid,
        "user_name": current_user.get('display_name', 'Anonymous')
    }
    
    cert_ref = db.collection('users').document(user_uid).collection('certificates').document()
    cert_ref.set(cert_data)
    
    # Also update user's certificate count
    db.collection('users').document(user_uid).update({"certificates_count": firestore.Increment(1)})
    
    cert_data['id'] = cert_ref.id
    return CertificateResponse(**cert_data)
