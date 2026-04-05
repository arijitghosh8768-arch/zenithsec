import hashlib
import ssl
import socket
import logging
from typing import Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)


async def scan_url(url: str) -> dict:
    """Perform comprehensive URL analysis."""
    result = {
        "url": url,
        "risk_score": 0,
        "risk_level": "low",
        "ssl_info": None,
        "whois_info": None,
        "threats": [],
        "reputation": "unknown",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    # SSL Check
    try:
        result["ssl_info"] = await _check_ssl(parsed.hostname)
    except Exception as e:
        result["threats"].append({"type": "ssl_error", "detail": str(e), "severity": "medium"})
        result["risk_score"] += 20

    # URL pattern analysis
    threats = _analyze_url_patterns(url)
    result["threats"].extend(threats)
    result["risk_score"] += len(threats) * 15

    # VirusTotal check
    if settings.VIRUSTOTAL_API_KEY:
        try:
            vt_result = await _virustotal_url_scan(url)
            result["reputation"] = vt_result.get("reputation", "unknown")
            if vt_result.get("malicious", 0) > 0:
                result["risk_score"] += 50
                result["threats"].append({
                    "type": "virustotal",
                    "detail": f"Flagged by {vt_result['malicious']} security vendors",
                    "severity": "high"
                })
        except Exception as e:
            logger.warning(f"VirusTotal scan failed: {e}")

    # WHOIS
    try:
        result["whois_info"] = _get_whois_info(parsed.hostname)
    except Exception:
        pass

    # Calculate risk level
    if result["risk_score"] >= 70:
        result["risk_level"] = "critical"
    elif result["risk_score"] >= 40:
        result["risk_level"] = "high"
    elif result["risk_score"] >= 20:
        result["risk_level"] = "medium"
    else:
        result["risk_level"] = "low"

    result["risk_score"] = min(result["risk_score"], 100)
    return result


async def _check_ssl(hostname: str) -> Optional[dict]:
    """Check SSL certificate details."""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            cert = s.getpeercert()
            return {
                "issuer": dict(x[0] for x in cert.get("issuer", [])),
                "subject": dict(x[0] for x in cert.get("subject", [])),
                "valid_from": cert.get("notBefore", ""),
                "valid_to": cert.get("notAfter", ""),
                "serial_number": cert.get("serialNumber", ""),
                "version": cert.get("version", 0),
            }
    except Exception:
        return None


def _analyze_url_patterns(url: str) -> list:
    """Analyze URL for suspicious patterns."""
    threats = []
    suspicious_patterns = [
        ("login", "Possible phishing - contains login keyword"),
        ("verify", "Possible phishing - contains verify keyword"),
        ("secure", "Possible phishing - contains secure keyword"),
        (".tk", "Suspicious TLD commonly used in phishing"),
        (".ml", "Suspicious TLD commonly used in phishing"),
        ("@", "URL contains @ sign - possible redirect attack"),
        (".exe", "URL points to executable file"),
        ("base64", "URL may contain encoded payload"),
    ]
    lower_url = url.lower()
    for pattern, desc in suspicious_patterns:
        if pattern in lower_url:
            threats.append({"type": "url_pattern", "detail": desc, "severity": "low"})
    return threats


async def _virustotal_url_scan(url: str) -> dict:
    """Scan URL using VirusTotal API."""
    url_id = hashlib.sha256(url.encode()).hexdigest()
    async with httpx.AsyncClient() as client:
        headers = {"x-apikey": settings.VIRUSTOTAL_API_KEY}
        # Submit URL for scanning
        await client.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url}
        )
        # Get results
        resp = await client.get(
            f"https://www.virustotal.com/api/v3/urls/{url_id}",
            headers=headers
        )
        if resp.status_code == 200:
            data = resp.json()
            stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            return {
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "reputation": "malicious" if stats.get("malicious", 0) > 0 else "clean"
            }
    return {"malicious": 0, "reputation": "unknown"}


def _get_whois_info(domain: str) -> Optional[dict]:
    """Get WHOIS information for a domain."""
    try:
        import whois
        w = whois.whois(domain)
        return {
            "registrar": str(w.registrar) if w.registrar else "Unknown",
            "creation_date": str(w.creation_date) if w.creation_date else "Unknown",
            "expiration_date": str(w.expiration_date) if w.expiration_date else "Unknown",
            "name_servers": w.name_servers if w.name_servers else [],
            "country": str(w.country) if w.country else "Unknown",
        }
    except Exception:
        return None
