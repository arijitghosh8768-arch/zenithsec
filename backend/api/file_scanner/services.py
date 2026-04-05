import hashlib
import logging
from datetime import datetime, timezone
from config.settings import settings
import httpx

logger = logging.getLogger(__name__)


async def scan_file(filename: str, content: bytes) -> dict:
    """Scan a file for malware and vulnerabilities."""
    md5 = hashlib.md5(content).hexdigest()
    sha1 = hashlib.sha1(content).hexdigest()
    sha256 = hashlib.sha256(content).hexdigest()

    result = {
        "filename": filename,
        "size": len(content),
        "hashes": {"md5": md5, "sha1": sha1, "sha256": sha256},
        "risk_score": 0,
        "risk_level": "clean",
        "detections": [],
        "file_type": _detect_file_type(filename, content),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }

    # Pattern-based detection
    detections = _pattern_scan(content, filename)
    result["detections"].extend(detections)
    result["risk_score"] += len(detections) * 20

    # VirusTotal
    if settings.VIRUSTOTAL_API_KEY:
        try:
            vt = await _virustotal_file_scan(sha256)
            if vt.get("malicious", 0) > 0:
                result["risk_score"] += 60
                result["detections"].append({
                    "type": "virustotal",
                    "detail": f"Detected by {vt['malicious']} engines",
                    "severity": "critical"
                })
        except Exception as e:
            logger.warning(f"VT file scan failed: {e}")

    if result["risk_score"] >= 60:
        result["risk_level"] = "malicious"
    elif result["risk_score"] >= 30:
        result["risk_level"] = "suspicious"
    elif result["risk_score"] > 0:
        result["risk_level"] = "low_risk"

    result["risk_score"] = min(result["risk_score"], 100)
    return result


def _detect_file_type(filename: str, content: bytes) -> str:
    """Detect file type from extension and magic bytes."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    magic = {
        b"\x4d\x5a": "PE Executable",
        b"\x7fELF": "ELF Executable",
        b"\x50\x4b\x03\x04": "ZIP Archive",
        b"\x25\x50\x44\x46": "PDF Document",
        b"\xd0\xcf\x11\xe0": "MS Office Document",
    }
    for sig, ftype in magic.items():
        if content[:len(sig)] == sig:
            return ftype
    return ext


def _pattern_scan(content: bytes, filename: str) -> list:
    """Scan file content for suspicious patterns (simplified YARA-like)."""
    detections = []
    text = content.decode("utf-8", errors="ignore").lower()

    patterns = [
        ("powershell -encodedcommand", "Encoded PowerShell command", "high"),
        ("invoke-expression", "PowerShell code execution", "high"),
        ("cmd.exe /c", "Command execution via cmd", "medium"),
        ("wget ", "File download command", "low"),
        ("curl ", "File download command", "low"),
        ("/etc/passwd", "Unix password file access", "high"),
        ("eval(", "Dynamic code evaluation", "medium"),
        ("exec(", "Dynamic code execution", "medium"),
        ("base64_decode", "Base64 decoding (obfuscation)", "medium"),
        ("document.cookie", "Cookie access (possible XSS)", "medium"),
    ]

    for pattern, desc, severity in patterns:
        if pattern in text:
            detections.append({"type": "pattern_match", "detail": desc, "severity": severity})

    # Check for suspicious file extensions
    dangerous_exts = [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".wsf", ".scr"]
    if any(filename.lower().endswith(ext) for ext in dangerous_exts):
        detections.append({"type": "file_type", "detail": "Potentially dangerous file type", "severity": "medium"})

    return detections


async def _virustotal_file_scan(sha256: str) -> dict:
    """Check file hash against VirusTotal."""
    async with httpx.AsyncClient() as client:
        headers = {"x-apikey": settings.VIRUSTOTAL_API_KEY}
        resp = await client.get(
            f"https://www.virustotal.com/api/v3/files/{sha256}",
            headers=headers
        )
        if resp.status_code == 200:
            stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            return {"malicious": stats.get("malicious", 0), "suspicious": stats.get("suspicious", 0)}
    return {"malicious": 0}
