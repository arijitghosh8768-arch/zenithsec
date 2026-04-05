from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class URLScanRequest(BaseModel):
    url: str = Field(..., min_length=1)


class ThreatInfo(BaseModel):
    type: str
    detail: str
    severity: str


class SSLInfo(BaseModel):
    issuer: Optional[dict] = None
    subject: Optional[dict] = None
    valid_from: str = ""
    valid_to: str = ""
    serial_number: str = ""
    version: int = 0


class WHOISInfo(BaseModel):
    registrar: str = "Unknown"
    creation_date: str = "Unknown"
    expiration_date: str = "Unknown"
    name_servers: List[str] = []
    country: str = "Unknown"


class URLScanResponse(BaseModel):
    url: str
    risk_score: int
    risk_level: str
    ssl_info: Optional[dict] = None
    whois_info: Optional[dict] = None
    threats: List[dict] = []
    reputation: str = "unknown"
    scanned_at: str
