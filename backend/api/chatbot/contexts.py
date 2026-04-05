import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

# Try to import Redis, fallback to memory cache if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis not installed. Using in-memory cache.")

# ============= Enums and Data Classes =============

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class ChatMessage:
    """Individual chat message with metadata"""
    role: MessageRole
    content: str
    timestamp: datetime
    tokens: int = 0
    message_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tokens": self.tokens,
            "message_id": self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessage":
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tokens=data.get("tokens", 0),
            message_id=data.get("message_id")
        )


@dataclass
class ConversationContext:
    """Complete conversation context for a session"""
    session_id: str
    user_id: Optional[int]
    messages: List[ChatMessage]
    topic_focus: Optional[str]
    difficulty: DifficultyLevel
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "topic_focus": self.topic_focus,
            "difficulty": self.difficulty.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        return cls(
            session_id=data["session_id"],
            user_id=data.get("user_id"),
            messages=[ChatMessage.from_dict(m) for m in data.get("messages", [])],
            topic_focus=data.get("topic_focus"),
            difficulty=DifficultyLevel(data.get("difficulty", "beginner")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )


# ============= Enhanced Security Topics Database =============

SECURITY_TOPICS = {
    # Web Security
    'sql injection': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['web security', 'OWASP Top 10', 'database', 'injection'],
        'resources': ['OWASP SQLi Cheat Sheet', 'PortSwigger SQLi Labs', 'sqlmap documentation'],
        'prerequisites': ['SQL basics', 'Web applications'],
        'related_topics': ['parameterized queries', 'input validation', 'stored procedures']
    },
    'sqli': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['web security', 'OWASP Top 10', 'database', 'injection'],
        'resources': ['OWASP SQLi Cheat Sheet', 'PortSwigger SQLi Labs'],
        'prerequisites': ['SQL basics'],
        'related_topics': ['blind sql injection', 'time-based attacks', 'out-of-band']
    },
    'xss': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['web security', 'client-side', 'OWASP Top 10'],
        'resources': ['OWASP XSS Prevention Cheat Sheet', 'XSS Hunter'],
        'prerequisites': ['JavaScript', 'HTML/DOM'],
        'related_topics': ['CSP', 'output encoding', 'DOM-based XSS']
    },
    'cross site scripting': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['web security', 'client-side', 'OWASP Top 10'],
        'resources': ['OWASP XSS Prevention'],
        'prerequisites': ['JavaScript'],
        'related_topics': ['reflected XSS', 'stored XSS', 'DOM XSS']
    },
    'csrf': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['web security', 'OWASP Top 10', 'session management'],
        'resources': ['OWASP CSRF Prevention', 'PortSwigger CSRF'],
        'prerequisites': ['Sessions', 'HTTP requests'],
        'related_topics': ['anti-CSRF tokens', 'same-site cookies']
    },
    'ssrf': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['web security', 'server-side', 'cloud security'],
        'resources': ['SSRF Bible', 'PortSwigger SSRF'],
        'prerequisites': ['Network requests', 'Cloud architecture'],
        'related_topics': ['internal network scanning', 'metadata APIs']
    },
    
    # Cryptography
    'encryption': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['cryptography', 'data protection'],
        'resources': ['Crypto 101', 'Practical Cryptography', 'Cryptopals'],
        'prerequisites': ['Mathematics basics', 'Computer science'],
        'related_topics': ['AES', 'RSA', 'ECC', 'symmetric encryption', 'asymmetric encryption']
    },
    'aes': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['cryptography', 'symmetric encryption'],
        'resources': ['AES specification', 'Crypto++ examples'],
        'prerequisites': ['Block ciphers', 'Encryption basics'],
        'related_topics': ['block modes', 'IV', 'padding oracles']
    },
    'rsa': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['cryptography', 'asymmetric encryption', 'PKI'],
        'resources': ['RSA algorithm explained', 'OpenSSL RSA'],
        'prerequisites': ['Number theory', 'Modular arithmetic'],
        'related_topics': ['prime numbers', 'key exchange', 'digital signatures']
    },
    'hashing': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['cryptography', 'integrity', 'passwords'],
        'resources': ['Password Hashing Cheat Sheet', 'Hashcat'],
        'prerequisites': ['One-way functions'],
        'related_topics': ['bcrypt', 'argon2', 'SHA256', 'rainbow tables']
    },
    
    # Malware & Threats
    'malware': {
        'difficulty': DifficultyLevel.BEGINNER,
        'tags': ['threat intelligence', 'reverse engineering', 'malware analysis'],
        'resources': ['Any.Run', 'VirusTotal', 'MalwareBazaar'],
        'prerequisites': ['Operating systems', 'Processes'],
        'related_topics': ['ransomware', 'trojans', 'worms', 'rootkits']
    },
    'ransomware': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['malware', 'threat intelligence', 'incident response'],
        'resources': ['No More Ransom', 'Ransomware Tracker'],
        'prerequisites': ['File systems', 'Cryptography basics'],
        'related_topics': ['backup strategies', 'decryption tools', 'TTPs']
    },
    'phishing': {
        'difficulty': DifficultyLevel.BEGINNER,
        'tags': ['social engineering', 'email security', 'awareness'],
        'resources': ['Phishing.org', 'OpenPhish'],
        'prerequisites': ['Email basics'],
        'related_topics': ['spear phishing', 'whaling', 'email authentication']
    },
    
    # Network Security
    'ddos': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['network security', 'availability', 'mitigation'],
        'resources': ['Cloudflare DDoS guide', 'NIST DDoS guide'],
        'prerequisites': ['TCP/IP', 'Network protocols'],
        'related_topics': ['amplification attacks', 'rate limiting', 'scrubbing centers']
    },
    'firewall': {
        'difficulty': DifficultyLevel.BEGINNER,
        'tags': ['network security', 'perimeter defense'],
        'resources': ['iptables tutorial', 'pfSense guide'],
        'prerequisites': ['Network packets', 'Ports'],
        'related_topics': ['WAF', 'NGFW', 'stateful inspection']
    },
    'ids': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['network security', 'monitoring', 'detection'],
        'resources': ['Snort manual', 'Suricata guide'],
        'prerequisites': ['Network protocols', 'Signatures'],
        'related_topics': ['IPS', 'signature-based detection', 'anomaly detection']
    },
    
    # Penetration Testing
    'penetration testing': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['methodology', 'ethical hacking', 'assessment'],
        'resources': ['PTES', 'OSCP guide', 'Metasploit Unleashed'],
        'prerequisites': ['Networking', 'Web security', 'Systems'],
        'related_topics': ['reconnaissance', 'exploitation', 'reporting']
    },
    'nmap': {
        'difficulty': DifficultyLevel.BEGINNER,
        'tags': ['scanning', 'reconnaissance', 'tools'],
        'resources': ['Nmap documentation', 'Nmap cheat sheet'],
        'prerequisites': ['TCP/IP', 'Ports'],
        'related_topics': ['port scanning', 'OS fingerprinting', 'script engine']
    },
    'metasploit': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['exploitation', 'tools', 'framework'],
        'resources': ['Metasploit guide', 'Metasploit minute'],
        'prerequisites': ['Vulnerabilities', 'Exploitation basics'],
        'related_topics': ['payloads', 'exploits', 'post-exploitation']
    },
    
    # Secure Coding
    'buffer overflow': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['memory safety', 'C/C++', 'exploitation'],
        'resources': ['Smashing The Stack', 'ROP tutorial'],
        'prerequisites': ['Assembly', 'Memory management'],
        'related_topics': ['stack overflow', 'heap overflow', 'ASLR', 'DEP']
    },
    'input validation': {
        'difficulty': DifficultyLevel.BEGINNER,
        'tags': ['secure coding', 'defense', 'best practices'],
        'resources': ['OWASP Input Validation', 'CWE-20'],
        'prerequisites': ['Programming basics'],
        'related_topics': ['sanitization', 'whitelist', 'blacklist']
    },
    
    # CTF & Practice
    'ctf': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['practice', 'competition', 'learning'],
        'resources': ['CTFtime', 'PicoCTF', 'HackTheBox', 'TryHackMe'],
        'prerequisites': ['Varied - depends on challenge'],
        'related_topics': ['pwn', 'reversing', 'crypto', 'web', 'forensics']
    },
    'hackthebox': {
        'difficulty': DifficultyLevel.INTERMEDIATE,
        'tags': ['practice', 'platform', 'hands-on'],
        'resources': ['HTB Academy', 'IPT walkthroughs'],
        'prerequisites': ['Basic security knowledge'],
        'related_topics': ['retired machines', 'pro labs', 'rank system']
    },
    
    # Cloud Security
    'cloud security': {
        'difficulty': DifficultyLevel.ADVANCED,
        'tags': ['cloud', 'devops', 'shared responsibility'],
        'resources': ['AWS Security Hub', 'Azure Security Center', 'GCP Security Command'],
        'prerequisites': ['Cloud basics', 'IAM'],
        'related_topics': ['container security', 'K8s security', 'serverless']
    },
    'kubernetes security': {
        'difficulty': DifficultyLevel.EXPERT,
        'tags': ['container', 'orchestration', 'devsecops'],
        'resources': ['K8s security guide', 'kube-bench', 'OPA'],
        'prerequisites': ['Kubernetes', 'Containers'],
        'related_topics': ['RBAC', 'network policies', 'pod security']
    }
}


# ============= Context Manager Class =============

class ContextManager:
    """Manages conversation contexts with Redis caching and memory fallback"""
    
    def __init__(self, redis_client=None, max_context_length: int = 20, max_tokens: int = 4000):
        """
        Initialize the context manager
        
        Args:
            redis_client: Redis client (optional, falls back to memory)
            max_context_length: Maximum number of messages to keep
            max_tokens: Maximum tokens in context window
        """
        self.redis = redis_client
        self.max_context_length = max_context_length
        self.max_tokens = max_tokens
        self._memory_cache: Dict[str, ConversationContext] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = 3600  # 1 hour default TTL
        
    async def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Retrieve context for a session"""
        # Try Redis first if available
        if self.redis and REDIS_AVAILABLE:
            try:
                data = self.redis.get(f"chat:context:{session_id}")
                if data:
                    context_dict = json.loads(data)
                    return ConversationContext.from_dict(context_dict)
            except Exception as e:
                print(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if session_id in self._memory_cache:
            expiry = self._cache_expiry.get(session_id)
            if expiry and expiry > datetime.now():
                return self._memory_cache[session_id]
            else:
                # Clean up expired
                del self._memory_cache[session_id]
                del self._cache_expiry[session_id]
        
        return None
    
    async def save_context(self, context: ConversationContext) -> bool:
        """Save conversation context"""
        context.updated_at = datetime.now()
        context_dict = context.to_dict()
        json_data = json.dumps(context_dict, default=str)
        
        # Save to Redis
        if self.redis and REDIS_AVAILABLE:
            try:
                self.redis.setex(
                    f"chat:context:{context.session_id}",
                    self._cache_ttl,
                    json_data
                )
            except Exception as e:
                print(f"Redis set error: {e}")
        
        # Save to memory cache
        self._memory_cache[context.session_id] = context
        self._cache_expiry[context.session_id] = datetime.now() + timedelta(seconds=self._cache_ttl)
        
        return True
    
    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        user_id: Optional[int] = None,
        tokens: int = 0
    ) -> ConversationContext:
        """Add a message to the conversation context"""
        # Get existing context or create new
        context = await self.get_context(session_id)
        
        if not context:
            context = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                messages=[],
                topic_focus=None,
                difficulty=DifficultyLevel.BEGINNER,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={}
            )
        
        # Create new message
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            tokens=tokens,
            message_id=self._generate_message_id(session_id)
        )
        
        # Add to context
        context.messages.append(message)
        
        # Trim if exceeds max length
        if len(context.messages) > self.max_context_length:
            context.messages = context.messages[-self.max_context_length:]
        
        # Update topic focus based on message
        if role == MessageRole.USER:
            detected_topic = self.detect_topic(content)
            if detected_topic:
                context.topic_focus = detected_topic
                context.difficulty = SECURITY_TOPICS.get(
                    detected_topic.lower(),
                    {}
                ).get('difficulty', DifficultyLevel.BEGINNER)
        
        # Save updated context
        await self.save_context(context)
        
        return context
    
    async def delete_context(self, session_id: str) -> bool:
        """Delete a conversation context"""
        # Delete from Redis
        if self.redis and REDIS_AVAILABLE:
            try:
                self.redis.delete(f"chat:context:{session_id}")
            except Exception as e:
                print(f"Redis delete error: {e}")
        
        # Delete from memory
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
            del self._cache_expiry[session_id]
        
        return True
    
    async def get_recent_messages(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get recent messages from a session"""
        context = await self.get_context(session_id)
        if not context:
            return []
        return context.messages[-limit:]
    
    async def get_context_window(
        self,
        session_id: str,
        max_tokens: Optional[int] = None
    ) -> List[Dict]:
        """
        Get context window optimized for token limits
        
        Returns list of messages that fit within token budget
        """
        context = await self.get_context(session_id)
        if not context:
            return []
        
        max_tokens = max_tokens or self.max_tokens
        messages = []
        current_tokens = 0
        
        # Start from most recent and go backwards
        for message in reversed(context.messages):
            # Rough token estimation (4 chars per token on average)
            message_tokens = len(message.content) // 4 + 50  # Add overhead
            
            if current_tokens + message_tokens <= max_tokens:
                messages.insert(0, {
                    "role": message.role.value,
                    "content": message.content
                })
                current_tokens += message_tokens
            else:
                break
        
        return messages
    
    def detect_topic(self, question: str) -> Optional[str]:
        """Detect security topic from user question"""
        lower_question = question.lower()
        
        # Sort by key length (longest first) to match more specific topics first
        sorted_topics = sorted(SECURITY_TOPICS.keys(), key=len, reverse=True)
        
        for topic in sorted_topics:
            if topic in lower_question:
                return topic
        
        return None
    
    def get_topic_info(self, topic: str) -> dict:
        """Get detailed information about a security topic"""
        topic_lower = topic.lower()
        
        if topic_lower in SECURITY_TOPICS:
            info = SECURITY_TOPICS[topic_lower].copy()
            info['topic'] = topic_lower
            return info
        
        return {
            'difficulty': DifficultyLevel.BEGINNER,
            'tags': ['general security'],
            'resources': ['General cybersecurity resources'],
            'prerequisites': [],
            'related_topics': [],
            'topic': topic_lower
        }
    
    def _generate_message_id(self, session_id: str) -> str:
        """Generate a unique message ID"""
        timestamp = datetime.now().timestamp()
        unique_string = f"{session_id}:{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    async def clear_expired(self) -> int:
        """Clear expired contexts from memory cache"""
        now = datetime.now()
        expired = [
            sid for sid, expiry in self._cache_expiry.items()
            if expiry < now
        ]
        
        for sid in expired:
            if sid in self._memory_cache:
                del self._memory_cache[sid]
            if sid in self._cache_expiry:
                del self._cache_expiry[sid]
        
        return len(expired)
    
    async def summarize_context(self, session_id: str) -> str:
        """Generate a summary of the conversation context"""
        context = await self.get_context(session_id)
        if not context or not context.messages:
            return "No conversation history available."
        
        # Extract key information
        message_count = len(context.messages)
        user_messages = [m for m in context.messages if m.role == MessageRole.USER]
        
        # Detect main topics discussed
        topics_discussed = set()
        for msg in user_messages[-5:]:  # Last 5 user messages
            topic = self.detect_topic(msg.content)
            if topic:
                topics_discussed.add(topic)
        
        summary = f"""
        Conversation Summary:
        - Total messages: {message_count}
        - Main topics: {', '.join(topics_discussed) if topics_discussed else 'General cybersecurity'}
        - Current difficulty level: {context.difficulty.value}
        - Session duration: {(datetime.now() - context.created_at).seconds // 60} minutes
        """
        
        return summary.strip()


# ============= Legacy Function (for backward compatibility) =============

def get_context_for_question(question: str) -> dict:
    """
    Legacy function - maintains backward compatibility with original code
    
    Args:
        question: User's question string
    
    Returns:
        Dictionary with difficulty, tags, and resources
    """
    context_manager = ContextManager()
    topic = context_manager.detect_topic(question)
    
    if topic:
        info = context_manager.get_topic_info(topic)
        return {
            'difficulty': info['difficulty'].value,
            'tags': info['tags'],
            'resources': info['resources'],
            'topic': topic
        }
    
    return {
        'difficulty': DifficultyLevel.BEGINNER.value,
        'tags': ['general security'],
        'resources': ['General cybersecurity resources'],
        'topic': None
    }


# ================== Export =============

__all__ = [
    'ContextManager',
    'ConversationContext',
    'ChatMessage',
    'MessageRole',
    'DifficultyLevel',
    'SECURITY_TOPICS',
    'get_context_for_question',
    'REDIS_AVAILABLE'
]
