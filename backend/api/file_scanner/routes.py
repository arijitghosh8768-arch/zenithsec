from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from config.security import get_current_user
from models.user import User
from api.file_scanner.services import scan_file

router = APIRouter(prefix="/api/file-scanner", tags=["File Scanner"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/scan")
async def scan(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 50MB.")
    result = await scan_file(file.filename or "unknown", content)
    return result
