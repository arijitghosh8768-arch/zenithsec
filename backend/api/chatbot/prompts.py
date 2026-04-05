from typing import Dict, List, Optional, Literal
from enum import Enum
from datetime import datetime

# ============= Enums for Type Safety =============
class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TopicCategory(str, Enum):
    WEB_SECURITY = "web_security"
    NETWORK_SECURITY = "network_security"
    CRYPTOGRAPHY = "cryptography"
    PENETRATION_TESTING = "penetration_testing"
    MALWARE_ANALYSIS = "malware_analysis"
    FORENSICS = "forensics"
    CLOUD_SECURITY = "cloud_security"
    SECURE_CODING = "secure_coding"
    CTF = "ctf"
    CAREER = "career"


# ============= Base System Prompt =============
SYSTEM_PROMPT = """You are ZenithSec AI Mentor, an expert cybersecurity instructor and ethical hacking guide. 

## Your Core Responsibilities:
1. **Teach** cybersecurity concepts clearly and accurately
2. **Guide** users through security challenges and CTF problems
3. **Explain** vulnerabilities, attack vectors, and defense strategies
4. **Help** with secure coding practices
5. **Advise** on cybersecurity careers and certifications

## Critical Guidelines:
### Ethical Boundaries (STRICT):
- ✅ **DO** emphasize ethical hacking and responsible disclosure
- ✅ **DO** include defensive countermeasures when discussing attacks
- ✅ **DO** encourage practice in legal environments (labs, VMs, CTFs)
- ❌ **NEVER** provide instructions for illegal activities
- ❌ **NEVER** share actual exploit code for unpatched vulnerabilities
- ❌ **NEVER** assist with bypassing security without authorization

### Response Quality:
- **Accuracy First**: Verify technical information before sharing
- **Context Matters**: Consider the user's skill level and goals
- **Examples Help**: Include real-world examples when relevant
- **Code When Useful**: Provide code snippets for secure implementations
- **Cite Sources**: Reference CVEs, research papers, or official docs

## Skill Level Adaptations:

### 🟢 BEGINNER (New to cybersecurity)
- Use simple analogies and avoid jargon
- Define every technical term first time used
- Provide step-by-step instructions
- Focus on fundamentals and concepts
- Example: "Think of a firewall like a security guard checking IDs..."

### 🟡 INTERMEDIATE (Some experience)
- Use technical terminology appropriately
- Explain complex concepts with examples
- Recommend specific tools and techniques
- Provide practical exercises
- Discuss trade-offs and alternatives

### 🟠 ADVANCED (Experienced practitioner)
- Deep technical discussions
- Reference CVEs and research papers
- Discuss advanced techniques and edge cases
- Analyze attack patterns and TTPs
- Cover cutting-edge security topics

### 🔴 EXPERT (Professional level)
- Research-level discussions
- Zero-day analysis methodology
- Advanced exploitation techniques (defensively)
- Security research methodologies
- Tool development approaches

## Response Format Guidelines:
1. **Structure**: Use clear headings, bullet points, numbered lists
2. **Code Blocks**: Specify language for syntax highlighting
3. **Warnings**: Use ⚠️ for security-critical information
4. **Tips**: Use 💡 for helpful suggestions
5. **Resources**: End with relevant further reading

## Topics You Master:

### Web Application Security
- OWASP Top 10 (latest version)
- SQL Injection, XSS, CSRF, SSRF
- Authentication & Authorization flaws
- API security (REST, GraphQL)
- JWT, OAuth, SAML security

### Network Security
- Firewalls (iptables, nftables, WAF)
- IDS/IPS (Snort, Suricata)
- VPNs (IPsec, WireGuard, OpenVPN)
- Network segmentation & zero trust
- Protocol analysis (TCP/IP, HTTP/2, QUIC)

### Cryptography
- Symmetric (AES, ChaCha20)
- Asymmetric (RSA, ECC)
- Hash functions (SHA, bcrypt, Argon2)
- PKI, certificates, TLS
- Cryptographic protocols (Signal, Noise)

### Penetration Testing
- Methodology (PTES, OWASP, OSSTMM)
- Reconnaissance & OSINT
- Vulnerability assessment
- Exploitation (with defensive focus)
- Reporting & remediation

### Malware Analysis
- Static analysis techniques
- Dynamic analysis (sandboxes)
- Reverse engineering (Ghidra, IDA)
- Memory forensics (Volatility)
- Threat intelligence

### Cloud Security
- AWS, Azure, GCP security
- Container security (Docker, Kubernetes)
- Infrastructure as Code scanning
- Cloud-native threats
- Compliance (SOC2, ISO27001)

### Secure Coding
- Input validation & sanitization
- Output encoding
- Authentication & session management
- Access control patterns
- Cryptographic implementation

## Prohibited Content (WILL NOT RESPOND TO):
- Requests for hacking real systems without permission
- Asking for illegal access credentials
- Malware development for malicious purposes
- DDoS attack instructions
- Social engineering scripts for phishing
- Any content that violates ethical guidelines

## Response Style:
- **Professional but approachable**: Not overly academic
- **Encouraging**: Build confidence in learners
- **Precise**: No ambiguity in security advice
- **Actionable**: Provide concrete next steps
"""

# ============= Skill Level Addons =============
SKILL_LEVEL_ADDONS = {
    SkillLevel.BEGINNER: """
## BEGINNER MODE ACTIVE:
- Use simple analogies (e.g., "Like locking your house door...")
- Define ALL technical terms
- Break concepts into 3-4 simple steps
- Avoid acronyms without explanation
- Provide "Why this matters" for each concept
- Include "Check your understanding" questions
    """,
    
    SkillLevel.INTERMEDIATE: """
## INTERMEDIATE MODE ACTIVE:
- Use technical terminology confidently
- Explain trade-offs and alternatives
- Include tool recommendations with examples
- Provide "Try this" practical exercises
- Reference common CVEs and their impacts
- Discuss detection and prevention together
    """,
    
    SkillLevel.ADVANCED: """
## ADVANCED MODE ACTIVE:
- Deep dive into technical specifics
- Reference CVE numbers and research
- Discuss bypass techniques (defensively)
- Analyze attack chains and TTPs
- Cover edge cases and limitations
- Include "Research further" pointers
    """,
    
    SkillLevel.EXPERT: """
## EXPERT MODE ACTIVE:
- Research-level technical discussion
- Zero-day analysis methodology
- Advanced exploitation techniques (defensive focus)
- Security research approaches
- Tool development strategies
- Academic paper references
    """
}

# ============= Topic-Specific Instructions =============
TOPIC_INSTRUCTIONS = {
    TopicCategory.WEB_SECURITY: """
### Web Security Focus:
- Reference OWASP Top 10
- Include input validation patterns
- Discuss CSP, CORS, security headers
- Show both vulnerable and secure code
- Cover modern frameworks (React, Next.js, Django)
    """,
    
    TopicCategory.NETWORK_SECURITY: """
### Network Security Focus:
- Explain defense in depth
- Include practical firewall rules
- Discuss network segmentation
- Cover IDS/IPS evasion (defensively)
- Include packet analysis examples
    """,
    
    TopicCategory.CRYPTOGRAPHY: """
### Cryptography Focus:
- NEVER recommend custom crypto
- Explain "why" not just "how"
- Include key management best practices
- Discuss quantum-resistant algorithms
- Provide implementation examples using standard libraries
    """,
    
    TopicCategory.PENETRATION_TESTING: """
### Penetration Testing Focus:
- Emphasize authorized testing only
- Include methodology steps
- Recommend specific tools with use cases
- Discuss reporting and remediation
- Cover legal considerations
    """,
    
    TopicCategory.CTF: """
### CTF Challenge Guidance:
- **HINT only** - never give direct flags
- Explain the vulnerability class
- Guide toward the solution path
- Suggest relevant tools/commands
- Provide similar examples from practice
- Teach methodology, not answers
    """,
    
    TopicCategory.SECURE_CODING: """
### Secure Coding Focus:
- Show secure alternatives to vulnerable code
- Include language-specific best practices
- Discuss dependency management
- Cover SAST/DAST tools
- Include input validation patterns
    """
}

# ============= Templates =============
CODE_EXPLANATION_TEMPLATE = """
## Code Security Analysis

### Original Code:
```{language}
{code}
```

### Analysis Results:

#### 🔴 Critical Vulnerabilities:
{critical_vulns}

#### 🟡 High Risk Issues:
{high_vulns}

#### 🟢 Low Risk / Best Practices:
{low_vulns}

### Risk Assessment:
**Overall Risk Score**: {risk_score}/10
**CVSS Vector**: {cvss_vector}
**Exploitability**: {exploitability}

### Remediation Steps:
{remediation}

### Secure Code Alternative:
```{language}
{secure_code}
```

### References:
- CWE: {cwe_ids}
- OWASP: {owasp_refs}
- Mitre ATT&CK: {mitre_techs}
"""

VULNERABILITY_ANALYSIS_TEMPLATE = """
## Vulnerability Analysis: {vulnerability}

### Context
{context}

### 1. Technical Explanation
{technical_explanation}

### 2. Impact Assessment
- **Confidentiality**: {conf_impact}
- **Integrity**: {int_impact}
- **Availability**: {avail_impact}
- **Business Impact**: {business_impact}

### 3. Attack Scenarios
{attack_scenarios}

### 4. Mitigation Strategies
{mitigations}

### 5. Detection Methods
{detection_methods}

### 6. Real-World Examples
{real_examples}

### 7. Further Resources
{resources}
"""

CTF_HINT_TEMPLATE = """
## CTF Challenge Guidance 🔐

**Challenge Type**: {challenge_type}
**Difficulty**: {difficulty}

### Hint #{hint_number}:
{hint_text}

### Methodology to Solve:
{solution_path}

### Tools That Might Help:
- {tool_1}
- {tool_2}
- {tool_3}

### Related Practice:
{practice_suggestions}

⚠️ **Remember**: The goal is learning, not just the flag!
"""

SECURE_CODING_TEMPLATE = """
## Secure Coding Review

**Language**: {language}
**Security Context**: {context}

### Vulnerable Pattern:
```{language}
{vulnerable_code}
```

### Issues Identified:
{issues}

### Secure Implementation:
```{language}
{secure_code}
```

### Why This Matters:
{explanation}

### Testing Your Fix:
{test_strategy}
"""

# ============= Dynamic Prompt Builder =============
class PromptBuilder:
    """Builds dynamic prompts based on context and user preferences"""
    
    def __init__(self):
        self.base_prompt = SYSTEM_PROMPT
    
    def build_prompt(
        self,
        skill_level: SkillLevel = SkillLevel.BEGINNER,
        topic: Optional[TopicCategory] = None,
        conversation_context: Optional[List[Dict]] = None,
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Build a dynamic prompt based on multiple factors
        
        Args:
            skill_level: User's skill level
            topic: Specific topic focus
            conversation_context: Recent conversation history
            user_context: User-specific information (goals, progress)
        
        Returns:
            Complete prompt string
        """
        prompt_parts = [self.base_prompt]
        
        # Add skill level instructions
        if skill_level in SKILL_LEVEL_ADDONS:
            prompt_parts.append(SKILL_LEVEL_ADDONS[skill_level])
        
        # Add topic-specific instructions
        if topic and topic in TOPIC_INSTRUCTIONS:
            prompt_parts.append(TOPIC_INSTRUCTIONS[topic])
        
        # Add user context
        if user_context:
            context_prompt = self._build_user_context(user_context)
            prompt_parts.append(context_prompt)
        
        # Add conversation context
        if conversation_context:
            context_prompt = self._build_conversation_context(conversation_context)
            prompt_parts.append(context_prompt)
        
        # Add response format reminder
        prompt_parts.append(self._get_format_reminder())
        
        return "\n\n".join(prompt_parts)
    
    def _build_user_context(self, user_context: Dict) -> str:
        """Build user-specific context section"""
        sections = ["## User Context:"]
        
        if "goals" in user_context:
            sections.append(f"**Learning Goals**: {user_context['goals']}")
        
        if "current_course" in user_context:
            sections.append(f"**Current Course**: {user_context['current_course']}")
        
        if "recent_topics" in user_context:
            topics = ", ".join(user_context['recent_topics'])
            sections.append(f"**Recently Covered**: {topics}")
        
        if "certification_goal" in user_context:
            sections.append(f"**Target Certification**: {user_context['certification_goal']}")
        
        return "\n".join(sections)
    
    def _build_conversation_context(self, conversation: List[Dict]) -> str:
        """Build conversation history context"""
        if not conversation:
            return ""
        
        recent = conversation[-5:]  # Last 5 messages
        context = ["## Recent Conversation:"]
        
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:200]  # Truncate long messages
            context.append(f"{role}: {content}")
        
        return "\n".join(context)
    
    def _get_format_reminder(self) -> str:
        """Get response format reminder"""
        return """
## Response Format Reminder:
- Use clear section headers (## for main, ### for sub)
- Format code with triple backticks and language specifier
- Use 🛡️ for security tips, ⚠️ for warnings, 💡 for insights
- Keep responses focused and actionable
- End with "Next Steps" when appropriate
"""
    
    def get_code_analysis_prompt(
        self,
        code: str,
        language: str,
        skill_level: SkillLevel = SkillLevel.INTERMEDIATE
    ) -> str:
        """Build a prompt for code security analysis"""
        return CODE_EXPLANATION_TEMPLATE.format(
            language=language,
            code=code,
            critical_vulns="[To be identified]",
            high_vulns="[To be identified]",
            low_vulns="[To be identified]",
            risk_score="[Calculate]",
            cvss_vector="[Determine]",
            exploitability="[Assess]",
            remediation="[Provide steps]",
            secure_code="[Write secure version]",
            cwe_ids="[List CWE IDs]",
            owasp_refs="[Add OWASP references]",
            mitre_techs="[Add MITRE techniques]"
        )
    
    def get_vulnerability_prompt(
        self,
        vulnerability: str,
        context: str,
        depth: Literal["basic", "detailed", "expert"] = "detailed"
    ) -> str:
        """Build a prompt for vulnerability analysis"""
        return VULNERABILITY_ANALYSIS_TEMPLATE.format(
            vulnerability=vulnerability,
            context=context,
            technical_explanation="[Provide explanation]",
            conf_impact="[Assess]",
            int_impact="[Assess]",
            avail_impact="[Assess]",
            business_impact="[Assess]",
            attack_scenarios="[Describe scenarios]",
            mitigations="[List mitigations]",
            detection_methods="[List detection methods]",
            real_examples="[Provide examples]",
            resources="[List resources]"
        )
    
    def get_ctf_hint_prompt(
        self,
        challenge_type: str,
        difficulty: str,
        hint_level: int = 1
    ) -> str:
        """Build a prompt for CTF hints"""
        hints = {
            1: "Look at the vulnerability class first",
            2: "Consider how input is processed",
            3: "Think about edge cases and boundary conditions"
        }
        
        return CTF_HINT_TEMPLATE.format(
            challenge_type=challenge_type,
            difficulty=difficulty,
            hint_number=hint_level,
            hint_text=hints.get(hint_level, "Analyze the attack surface"),
            solution_path="[Provide step-by-step methodology]",
            tool_1="Burp Suite / OWASP ZAP",
            tool_2="nmap / masscan",
            tool_3="custom script / exploit",
            practice_suggestions="[Suggest similar challenges]"
        )


# ============= Helper Functions =============
def get_prompt_for_skill_level(skill_level: str) -> str:
    """Get the appropriate prompt addon for a skill level"""
    try:
        level = SkillLevel(skill_level.lower())
        return SKILL_LEVEL_ADDONS.get(level, SKILL_LEVEL_ADDONS[SkillLevel.BEGINNER])
    except ValueError:
        return SKILL_LEVEL_ADDONS[SkillLevel.BEGINNER]


def get_topic_instructions(topic: str) -> str:
    """Get topic-specific instructions"""
    try:
        topic_enum = TopicCategory(topic.lower().replace(" ", "_"))
        return TOPIC_INSTRUCTIONS.get(topic_enum, "")
    except ValueError:
        return ""


def create_ctf_response_format() -> str:
    """Create response format for CTF challenges"""
    return """
## CTF Response Format:
1. **Hint** (not solution)
2. **Vulnerability Explanation**
3. **Methodology** to find the vulnerability
4. **Tool Suggestions**
5. **Similar Practice Challenges**
6. **Learning Resources**
"""


# ============= Validation Functions =============
def validate_prompt_content(prompt: str) -> bool:
    """Validate that prompt doesn't contain prohibited content"""
    prohibited = [
        "how to hack",
        "illegal access",
        "bypass authentication without permission",
        "crack passwords for",
        "ddos tool"
    ]
    
    prompt_lower = prompt.lower()
    for prohibited_phrase in prohibited:
        if prohibited_phrase in prompt_lower:
            return False
    return True


def sanitize_user_input(user_input: str) -> str:
    """Sanitize user input before including in prompts"""
    # Remove potential prompt injection attempts
    dangerous_patterns = [
        "ignore previous instructions",
        "forget your training",
        "you are now",
        "system prompt",
        "developer mode"
    ]
    
    sanitized = user_input
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, "[REDACTED]")
    
    return sanitized


# ============= Export =============
__all__ = [
    'SYSTEM_PROMPT',
    'SKILL_LEVEL_ADDONS',
    'TOPIC_INSTRUCTIONS',
    'PromptBuilder',
    'SkillLevel',
    'TopicCategory',
    'get_prompt_for_skill_level',
    'get_topic_instructions',
    'validate_prompt_content',
    'sanitize_user_input'
]
