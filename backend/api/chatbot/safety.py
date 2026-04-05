import re
import logging
import hashlib
import asyncio
from typing import List, Tuple, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

# ============= Enums =============

class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentCategory(str, Enum):
    MALICIOUS_INTENT = "malicious_intent"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    PROMPT_INJECTION = "prompt_injection"
    PII_LEAK = "pii_leak"
    TOXIC_CONTENT = "toxic_content"
    ILLEGAL_ACTIVITY = "illegal_activity"
    EXPLOIT_CODE = "exploit_code"
    SOCIAL_ENGINEERING = "social_engineering"
    SAFE_CONTENT = "safe_content"


@dataclass
class SafetyResult:
    """Result of safety check"""
    is_safe: bool
    risk_level: RiskLevel
    categories: List[ContentCategory]
    confidence: float  # 0.0 to 1.0
    message: str
    redacted_content: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


# ============= Enhanced Pattern Definitions =============

# Malicious intent patterns (expanded)
MALICIOUS_PATTERNS = {
    # Hacking attempts
    "unauthorized_access": [
        r"how\s+to\s+hack\s+(into\s+)?(someone|a\s+website|a\s+system|a\s+server)",
        r"break\s+into\s+(someone'?s?\s+)?(account|system|computer)",
        r"crack\s+(someone'?s?\s+)?(password|account|wifi)",
        r"bypass\s+(login|authentication|2fa|mfa)\s+without\s+permission",
        r"access\s+(someone'?s?\s+)?(email|messages|data|files)\s+illegally",
    ],
    
    # Data theft
    "data_theft": [
        r"steal\s+(someone'?s?\s+)?(password|credential|data|identity|information)",
        r"extract\s+(customer|user)\s+(data|information)\s+without\s+consent",
        r"dump\s+(database|password)\s+illegally",
        r"scrape\s+(personal|private)\s+data\s+without\s+permission",
    ],
    
    # Malware creation
    "malware": [
        r"create\s+(a\s+)?(virus|malware|trojan|ransomware|worm|rootkit)",
        r"build\s+(a\s+)?(keylogger|rat|backdoor)",
        r"write\s+ransomware\s+(for|to)\s+(encrypt|lock)\s+files",
        r"develop\s+malware\s+to\s+(spread|infect|damage)",
    ],
    
    # Attack execution
    "attacks": [
        r"ddos\s+attack\s+(on|against)\s+(a\s+)?(website|server|network)",
        r"launch\s+sql\s+injection\s+on\s+live\s+site",
        r"perform\s+xss\s+attack\s+on\s+real\s+website",
        r"execute\s+code\s+on\s+(someone'?s?\s+)?server\s+illegally",
        r"penetration\s+test\s+without\s+authorization",
    ],
    
    # Exploit development (for malicious purposes)
    "exploit_dev": [
        r"exploit\s+(a\s+)?(real|live|production)\s+(vulnerability|bug|system)",
        r"develop\s+exploit\s+for\s+unpatched\s+vulnerability",
        r"zero[-\s]day\s+exploit\s+(for\s+profit|to\s+sell)",
        r"weaponize\s+(vulnerability|exploit)",
    ],
    
    # Social engineering
    "social_engineering": [
        r"phishing\s+(campaign|email|page)\s+to\s+steal",
        r"create\s+fake\s+(login|website|page)\s+to\s+trick",
        r"impersonate\s+(someone|a\s+company)\s+to\s+get\s+info",
        r"social\s+engineering\s+(script|template|guide)\s+to\s+manipulate",
    ],
    
    # Illegal activities
    "illegal": [
        r"buy\s+(stolen|cracked|illegal)\s+(credentials|data|accounts)",
        r"sell\s+(exploit|vulnerability|access)\s+to\s+dark\s+web",
        r"hire\s+hacker\s+to\s+(attack|breach|compromise)",
        r"dark\s+web\s+(market|marketplace)\s+for\s+hacking\s+tools",
    ],
}

# Prompt injection and jailbreak patterns
JAILBREAK_PATTERNS = [
    r"ignore\s+(all|previous|above)\s+(instructions|commands|rules|guidelines)",
    r"forget\s+(your|previous)\s+(training|instructions|constraints)",
    r"you\s+are\s+now\s+(a|an)\s+(evil|malicious|unrestricted|hacker)\s+(version|mode)",
    r"act\s+as\s+if\s+you\s+have\s+no\s+(rules|restrictions|boundaries)",
    r"developer\s+mode\s+(override|enabled|bypass)",
    r"system\s+prompt\s+override",
    r"pretend\s+you\s+are\s+(a\s+)?(different|another)\s+(AI|assistant)",
    r"no\s+(safety|security|ethical)\s+(restrictions|guidelines|protocols)",
    r"you\s+must\s+obey\s+my\s+commands\s+completely",
    r"disregard\s+(your|standard)\s+(protocol|procedure|rules)",
]

# Exploit code indicators (code patterns that might be malicious)
EXPLOIT_CODE_PATTERNS = {
    "sql_injection": [
        r"(\'|\")\s*(or|and)\s+1\s*=\s*1\s*--",
        r"union\s+select\s+.*from\s+information_schema",
        r"into\s+(outfile|dumpfile)\s+['\"]",
    ],
    "command_injection": [
        r"\$\s*\(\s*.*\s*\)",
        r"`.*`",
        r"\|.*\|\s*.*",
        r";\s*(wget|curl|nc|bash|sh|python|perl)",
        r"os\.system\s*\(['\"]",
    ],
    "xss": [
        r"<script>.*</script>",
        r"javascript:\s*.*",
        r"onerror=\s*['\"]alert\s*\(",
        r"onload=\s*['\"]alert\s*\(",
    ],
    "reverse_shell": [
        r"nc\s+-e\s+/bin/sh",
        r"bash\s+-i\s+>&\s+/dev/tcp/",
        r"python\s+-c\s+['\"]import\s+socket",
        r"rm\s+/tmp/f;mkfifo\s+/tmp/f",
    ],
}

# Toxic content patterns
TOXIC_PATTERNS = [
    r"\b(fuck|shit|damn|hell|asshole|bastard|cunt|dick|pussy)\b",
    r"\b(kill|die|murder|suicide)\b.*\b(you|yourself|them)\b",
    r"\b(terrorist|bomb|attack)\b.*\b(how|make|create)\b",
    r"racial\s+slurs?|hate\s+speech|racist",
]

# ============= PII Patterns (Enhanced) =============

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone_us": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "phone_intl": r"\+\d{1,3}[-.\s]?\d{1,14}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "mac_address": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b",
    "api_key": r"[a-zA-Z0-9]{32,}\b",
    "jwt_token": r"eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*",
    "password_in_text": r"password\s*[=:]\s*['\"]?\S+['\"]?",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "github_token": r"gh[ps]_[a-zA-Z0-9]{36}",
}

# ============= Safety Response Templates =============

SAFETY_RESPONSES = {
    RiskLevel.HIGH: {
        "message": "🛡️ **Safety Notice**: I can't assist with this request as it appears to involve potentially harmful or illegal activities.",
        "guidance": "\n\nI'm here to help with **ethical cybersecurity education**. Please rephrase your question to focus on:\n"
                    "- **Defensive security** techniques\n"
                    "- **Authorized** penetration testing\n"
                    "- **Educational** examples in controlled environments\n"
                    "- **Security best practices** and compliance\n\n"
                    "What legitimate security topic can I help you with today?"
    },
    RiskLevel.MEDIUM: {
        "message": "⚠️ **Caution**: Your request raises some security concerns.",
        "guidance": "\n\nI'll provide educational information, but please ensure you:\n"
                    "- Only test systems you **own** or have **written permission** to test\n"
                    "- Practice in **legal sandboxes** (HackTheBox, TryHackMe, OWASP WebGoat)\n"
                    "- Use this knowledge for **defensive purposes**\n\n"
                    "Let me refocus on the educational aspects of your question."
    },
    RiskLevel.LOW: {
        "message": "💡 **Note**: I'll provide security education, but remember ethical boundaries.",
        "guidance": "\n\n*Information provided for educational purposes only. Always obtain proper authorization.*\n"
    }
}

ETHICAL_DISCLAIMER = (
    "\n\n---\n"
    "🛡️ **Ethical Security Reminder:**\n"
    "The information provided is for **educational purposes** and **authorized security testing only**.\n"
    "Always:\n"
    "• Obtain written permission before testing systems\n"
    "• Practice in isolated lab environments\n"
    "• Follow responsible disclosure practices\n"
    "• Respect privacy and applicable laws\n\n"
    "*Security is about protection, not destruction.*"
)

# ============= Core Safety Functions =============

class SafetyChecker:
    """Comprehensive safety checker for AI chat interactions"""
    
    def __init__(self, enable_redaction: bool = True):
        self.enable_redaction = enable_redaction
        self._rate_limit_tracker: Dict[str, List[datetime]] = defaultdict(list)
        self._max_requests_per_minute = 10
        self._blocked_ips: Set[str] = set()
        
    def check_malicious_intent(self, message: str) -> Tuple[bool, List[ContentCategory], float]:
        """
        Check for malicious intent in the message.
        
        Returns:
            Tuple of (is_malicious, detected_categories, confidence_score)
        """
        detected_categories = []
        confidence_scores = []
        
        message_lower = message.lower()
        
        for category, patterns in MALICIOUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    detected_categories.append(ContentCategory(category))
                    confidence_scores.append(0.8)  # Base confidence
                    break
        
        # Check for jailbreak attempts
        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                detected_categories.append(ContentCategory.JAILBREAK_ATTEMPT)
                confidence_scores.append(0.9)
                break
        
        # Check for exploit code
        for exploit_type, patterns in EXPLOIT_CODE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    detected_categories.append(ContentCategory.EXPLOIT_CODE)
                    confidence_scores.append(0.7)
                    break
        
        # Check for toxic content
        for pattern in TOXIC_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                detected_categories.append(ContentCategory.TOXIC_CONTENT)
                confidence_scores.append(0.6)
                break
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        is_malicious = len(detected_categories) > 0
        
        # Remove duplicates
        detected_categories = list(dict.fromkeys(detected_categories))
        
        if is_malicious:
            logger.warning(f"Malicious intent detected: {detected_categories}, confidence: {avg_confidence}")
            
        return is_malicious, detected_categories, avg_confidence
    
    def redact_pii(self, text: str) -> str:
        """Redact personally identifiable information from text."""
        if not self.enable_redaction:
            return text
            
        redacted = text
        
        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.finditer(pattern, redacted, re.IGNORECASE)
            for match in matches:
                # Replace with redaction marker
                placeholder = f"[REDACTED_{pii_type.upper()}]"
                redacted = redacted.replace(match.group(), placeholder)
                
        return redacted
    
    def check_pii_leak(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains PII and return found PII types."""
        found_pii = []
        
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found_pii.append(pii_type)
                
        return len(found_pii) > 0, found_pii
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, int]:
        """Check if user has exceeded rate limit."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        self._rate_limit_tracker[user_id] = [
            ts for ts in self._rate_limit_tracker[user_id] 
            if ts > one_minute_ago
        ]
        
        request_count = len(self._rate_limit_tracker[user_id])
        is_rate_limited = request_count >= self._max_requests_per_minute
        
        if not is_rate_limited:
            self._rate_limit_tracker[user_id].append(now)
            
        return is_rate_limited, request_count
    
    def detect_prompt_injection(self, message: str) -> Tuple[bool, float]:
        """Detect potential prompt injection attempts."""
        injection_patterns = [
            r"ignore\s+(previous|above)\s+instructions",
            r"you\s+are\s+.*\s+now\s+",
            r"override\s+.*\s+system",
            r"pretend\s+you\s+are\s+",
            r"new\s+instruction:",
            r"role[-:]?\s*(play|change|switch)",
        ]
        
        message_lower = message.lower()
        confidence = 0
        
        for pattern in injection_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                confidence = max(confidence, 0.7)
                
        return confidence > 0.5, confidence
    
    def get_safety_response(self, risk_level: RiskLevel) -> str:
        """Get appropriate safety response based on risk level."""
        if risk_level in SAFETY_RESPONSES:
            return f"{SAFETY_RESPONSES[risk_level]['message']}{SAFETY_RESPONSES[risk_level]['guidance']}"
        return SAFETY_RESPONSES[RiskLevel.MEDIUM]['message'] + SAFETY_RESPONSES[RiskLevel.MEDIUM]['guidance']
    
    def add_ethical_disclaimer(self, response: str, force: bool = False) -> str:
        """Add ethical disclaimer to security-related responses."""
        security_keywords = [
            "exploit", "vulnerability", "attack", "payload", "injection", 
            "bypass", "bypassing", "shell", "reverse shell", "backdoor",
            "privilege escalation", "cracking", "bruteforce", "enumeration"
        ]
        
        if force or any(kw in response.lower() for kw in security_keywords):
            # Only add if not already present
            if "ethical reminder" not in response.lower():
                return response + ETHICAL_DISCLAIMER
        return response
    
    def validate_response(self, response: str) -> Tuple[bool, List[str]]:
        """Validate that the AI response is safe."""
        warnings = []
        
        # Check for leaked PII in response
        has_pii, pii_types = self.check_pii_leak(response)
        if has_pii:
            warnings.append(f"Response contains redacted PII: {', '.join(pii_types)}")
            response = self.redact_pii(response)
            
        # Check for dangerous content in response
        is_malicious, categories, _ = self.check_malicious_intent(response)
        if is_malicious:
            warnings.append(f"Response flagged for: {[c.value for c in categories]}")
            
        # Check for incomplete safety warnings
        if any(kw in response.lower() for kw in ["hack", "exploit", "bypass"]):
            if "authorization" not in response.lower() and "permission" not in response.lower():
                warnings.append("Response missing ethical authorization reminder")
                
        return len(warnings) == 0, warnings
    
    async def comprehensive_check(
        self, 
        message: str, 
        user_id: str, 
        ip_address: Optional[str] = None
    ) -> SafetyResult:
        """Perform comprehensive safety check on user message."""
        
        # Check rate limiting
        is_rate_limited, request_count = self.check_rate_limit(user_id)
        if is_rate_limited:
            return SafetyResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM,
                categories=[ContentCategory.SAFE_CONTENT],
                confidence=1.0,
                message=f"Rate limit exceeded. Max {self._max_requests_per_minute} requests per minute.",
                warnings=[f"You have made {request_count} requests in the last minute"]
            )
        
        # Check for malicious intent
        is_malicious, categories, confidence = self.check_malicious_intent(message)
        
        # Check for prompt injection
        is_injection, injection_confidence = self.detect_prompt_injection(message)
        if is_injection:
            categories.append(ContentCategory.PROMPT_INJECTION)
            confidence = max(confidence, injection_confidence)
        
        # Check for PII
        has_pii, pii_types = self.check_pii_leak(message)
        
        # Redact PII if enabled
        redacted_message = self.redact_pii(message) if has_pii else None
        
        # Determine risk level
        risk_level = RiskLevel.SAFE
        if is_malicious or is_injection:
            risk_level = RiskLevel.HIGH if confidence > 0.8 else RiskLevel.MEDIUM
        elif has_pii:
            risk_level = RiskLevel.LOW
            
        # Prepare warning messages
        warnings = []
        if is_malicious:
            warnings.append(f"Detected potentially harmful intent (confidence: {confidence:.2f})")
        if is_injection:
            warnings.append("Possible prompt injection attempt detected")
        if has_pii:
            warnings.append(f"Redacted personal information: {', '.join(pii_types)}")
            
        return SafetyResult(
            is_safe=risk_level == RiskLevel.SAFE,
            risk_level=risk_level,
            categories=categories,
            confidence=confidence,
            message=self.get_safety_response(risk_level) if not risk_level == RiskLevel.SAFE else "Content passed safety check",
            redacted_content=redacted_message,
            warnings=warnings
        )


# ============= Legacy Functions (Backward Compatible) =============

def check_malicious_intent(message: str) -> bool:
    """Legacy function - backward compatibility"""
    checker = SafetyChecker()
    is_malicious, _, _ = checker.check_malicious_intent(message)
    return is_malicious


def get_safety_response() -> str:
    """Legacy function - backward compatibility"""
    checker = SafetyChecker()
    return checker.get_safety_response(RiskLevel.HIGH)


def redact_pii(text: str) -> str:
    """Legacy function - backward compatibility"""
    checker = SafetyChecker()
    return checker.redact_pii(text)


def add_ethical_disclaimer(response: str, needs_disclaimer: bool = False) -> str:
    """Legacy function - backward compatibility"""
    checker = SafetyChecker()
    return checker.add_ethical_disclaimer(response, needs_disclaimer)


# ============= FastAPI Dependency =============

async def get_safety_checker() -> SafetyChecker:
    """FastAPI dependency for safety checker"""
    return SafetyChecker()
