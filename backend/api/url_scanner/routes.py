from fastapi import APIRouter, Depends
from config.security import get_current_user
from models.user import User
from api.url_scanner.schemas import URLScanRequest, URLScanResponse
from api.url_scanner.services import scan_url

router = APIRouter(prefix="/api/url-scanner", tags=["URL Scanner"])


@router.post("/scan", response_model=URLScanResponse)
async def scan(request: URLScanRequest, current_user: User = Depends(get_current_user)):
    result = await scan_url(request.url)
    return URLScanResponse(**result)
