from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# ============= Enums for Type Safety =============
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ============= Request Schemas =============
class ChatRequest(BaseModel):
    """Request model for sending a message to AI mentor"""
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=5000,
        description="User's message to the AI mentor"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for continuing existing conversation"
    )
    context: Optional[dict] = Field(
        None,
        description="Additional context like current lesson, skill level"
    )

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Sanitize and validate message content"""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Check for empty after sanitization
        if not v.strip():
            raise ValueError('Message cannot be empty or only whitespace')
        return v


class StreamChatRequest(BaseModel):
    """Request model for streaming chat responses"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    stream: bool = Field(True, description="Enable streaming response")


# ============= Response Schemas =============
class ChatResponse(BaseModel):
    """Response model for regular chat"""
    response: str = Field(..., description="AI mentor's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    message_id: Optional[str] = Field(None, description="Unique message identifier")
    tokens_used: int = Field(0, description="Total tokens consumed")
    processing_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    safety_check_passed: bool = Field(True, description="Whether content passed safety filters")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "SQL injection occurs when...",
                "session_id": "abc123",
                "message_id": "msg_456",
                "tokens_used": 150,
                "processing_time_ms": 1200,
                "safety_check_passed": True
            }
        }


class StreamChunkResponse(BaseModel):
    """Response model for streaming chunks"""
    chunk: str = Field(..., description="Partial response chunk")
    done: bool = Field(False, description="Whether streaming is complete")
    session_id: Optional[str] = None
    message_id: Optional[str] = None


# ============= Message & History Schemas =============
class ChatMessage(BaseModel):
    """Individual chat message model"""
    id: Optional[int] = None
    role: MessageRole = Field(..., description="user, assistant, or system")
    content: str = Field(..., min_length=1, max_length=10000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tokens: Optional[int] = Field(None, description="Token count for this message")

    class Config:
        from_attributes = True


class ChatHistoryItem(BaseModel):
    """History item for list views (backward compatible)"""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(...)
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Complete chat history response"""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int
    created_at: datetime
    updated_at: datetime


# ============= Session Management Schemas =============
class SessionResponse(BaseModel):
    """Response model for session information"""
    id: int
    session_id: str = Field(..., description="Public session identifier (UUID)")
    title: str = Field(..., max_length=200)
    user_id: Optional[int] = None
    message_count: int = Field(0, description="Number of messages in session")
    created_at: datetime
    updated_at: datetime
    last_message_preview: Optional[str] = Field(None, max_length=100)

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Create a new chat session"""
    title: Optional[str] = Field("New Chat", max_length=200)
    skill_level: Optional[SkillLevel] = SkillLevel.BEGINNER
    context_topic: Optional[str] = Field(None, description="Topic focus for this session")


class SessionUpdate(BaseModel):
    """Update existing session"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    archived: Optional[bool] = None
    skill_level: Optional[SkillLevel] = None


class SessionListResponse(BaseModel):
    """Paginated session list response"""
    sessions: List[SessionResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


# ============= Error Response Schemas =============
class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error description")
    code: Optional[str] = Field(None, description="Error code for client handling")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = False
    error: str = Field(..., description="Primary error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error list")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for debugging")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid message content",
                "details": [{"field": "message", "message": "Message exceeds maximum length"}],
                "status_code": 400,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


# ============= Context & Metadata Schemas =============
class ChatContext(BaseModel):
    """Context information for AI responses"""
    skill_level: SkillLevel = SkillLevel.BEGINNER
    current_topic: Optional[str] = None
    recent_messages: List[ChatMessage] = Field(default_factory=list, max_items=20)
    user_preferences: Optional[dict] = Field(None, description="User-specific preferences")


class TokenUsage(BaseModel):
    """Token usage tracking"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


# ============= WebSocket Schemas =============
class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: Literal["message", "ping", "typing", "error"]
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TypingIndicator(BaseModel):
    """Typing indicator for real-time feedback"""
    is_typing: bool
    session_id: str
    user_id: Optional[int] = None
