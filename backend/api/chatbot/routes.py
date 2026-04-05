# File: backend/api/chatbot/routes.py

import uuid
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from datetime import datetime, timedelta

from config.database import get_db
from config.security import get_current_user, get_current_user_ws
from models.user import User
from models.learning import ChatSession, ChatMessage
from api.chatbot.schemas import (
    ChatRequest, ChatResponse, SessionResponse,
    SessionCreate, SessionUpdate, ChatHistoryItem,
    ErrorResponse, StreamChunkResponse, ChatHistoryResponse
)
from api.chatbot.ai_engine import get_ai_engine, AIEngine
from api.chatbot.safety import SafetyChecker, get_safety_checker
from api.chatbot.contexts import ContextManager
from api.chatbot.prompts import SkillLevel

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# ============= Rate Limiting =============
from collections import defaultdict
from datetime import datetime

_rate_limit_tracker: dict = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 20

def check_rate_limit(user_id: int) -> tuple[bool, int]:
    """Check if user has exceeded rate limit"""
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    
    # Clean old entries
    _rate_limit_tracker[user_id] = [
        ts for ts in _rate_limit_tracker[user_id] 
        if ts > one_minute_ago
    ]
    
    request_count = len(_rate_limit_tracker[user_id])
    is_limited = request_count >= MAX_REQUESTS_PER_MINUTE
    
    if not is_limited:
        _rate_limit_tracker[user_id].append(now)
    
    return is_limited, request_count


# ============= Helper Functions =============

async def get_or_create_session(
    session_id: Optional[str],
    user_id: int,
    db: AsyncSession,
    title: Optional[str] = None
) -> ChatSession:
    """Get existing session or create new one"""
    session = None
    
    if session_id:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()
    
    if not session:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "New Chat"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    # Update last activity
    session.updated_at = datetime.utcnow()
    await db.commit()
    
    return session


async def save_message(
    db: AsyncSession,
    session_id: int,
    role: str,
    content: str,
    tokens_used: int = 0,
    message_id: Optional[str] = None
) -> ChatMessage:
    """Save a message to database"""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tokens_used=tokens_used,
        message_id=message_id or str(uuid.uuid4())
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_history(
    db: AsyncSession,
    session_id: int,
    limit: int = 20
) -> List[ChatMessage]:
    """Get conversation history for a session"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return result.scalars().all()


async def cleanup_old_sessions(db: AsyncSession, days: int = 30):
    """Delete sessions older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get old sessions
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.updated_at < cutoff_date)
    )
    old_sessions = result.scalars().all()
    
    for session in old_sessions:
        await db.delete(session)
    
    await db.commit()
    return len(old_sessions)


# ============= WebSocket Connection Manager =============

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Add connection for user"""
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove connection for user"""
        async with self._lock:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
    
    async def send_message(self, user_id: int, message: dict):
        """Send message to all connections of a user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")

manager = ConnectionManager()


# ============= REST Endpoints =============

@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Send a message to the AI mentor and get a response
    """
    start_time = datetime.utcnow()
    
    # Rate limiting
    is_limited, request_count = check_rate_limit(current_user.id)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {MAX_REQUESTS_PER_MINUTE} requests per minute"
        )
    
    # Get safety checker
    safety_checker = await get_safety_checker()
    
    # Comprehensive safety check
    safety_result = await safety_checker.comprehensive_check(
        message=request.message,
        user_id=str(current_user.id)
    )
    
    if not safety_result.is_safe:
        return ChatResponse(
            response=safety_result.message,
            session_id=request.session_id or "",
            tokens_used=0,
            safety_check_passed=False,
            processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
        )
    
    # Get or create session
    session = await get_or_create_session(
        session_id=request.session_id,
        user_id=current_user.id,
        db=db,
        title=request.message[:50] if not request.session_id else None
    )
    
    # Save user message (redacted)
    clean_message = safety_checker.redact_pii(request.message)
    await save_message(
        db=db,
        session_id=session.id,
        role="user",
        content=clean_message,
        message_id=str(uuid.uuid4())
    )
    
    # Get conversation history
    history = await get_conversation_history(db, session.id, limit=20)
    
    # Get AI Engine
    ai_engine = await get_ai_engine()
    
    # Determine skill level from user profile (convert string to enum)
    skill_level_map = {
        "beginner": SkillLevel.BEGINNER,
        "intermediate": SkillLevel.INTERMEDIATE,
        "advanced": SkillLevel.ADVANCED
    }
    skill_level = skill_level_map.get(current_user.skill_level, SkillLevel.BEGINNER)
    
    # Get AI response with full context
    try:
        ai_response = await ai_engine.get_response(
            message=clean_message,
            session_id=session.session_id,
            user_id=current_user.id,
            skill_level=skill_level,
            stream=False
        )
        
        response_text = ai_response["content"]
        tokens_used = ai_response.get("tokens_used", 0)
        
        # Save assistant message
        await save_message(
            db=db,
            session_id=session.id,
            role="assistant",
            content=response_text,
            tokens_used=tokens_used,
            message_id=str(uuid.uuid4())
        )
        
        # Update session title if this is first message
        if len(history) == 0:
            # Generate title from first few words
            title = clean_message[:50] + ("..." if len(clean_message) > 50 else "")
            session.title = title
            await db.commit()
        
        # Send notification via WebSocket if user is connected
        await manager.send_message(
            user_id=current_user.id,
            message={
                "type": "new_message",
                "session_id": session.session_id,
                "message_preview": response_text[:100]
            }
        )
        
        return ChatResponse(
            response=response_text,
            session_id=session.session_id,
            tokens_used=tokens_used,
            safety_check_passed=True,
            processing_time_ms=ai_response.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        logger.error(f"AI Engine error: {e}")
        
        # Return fallback response
        fallback_response = ai_engine._fallback_response([{"role": "user", "content": request.message}], str(e))
        
        # Save fallback response
        await save_message(
            db=db,
            session_id=session.id,
            role="assistant",
            content=fallback_response["content"],
            tokens_used=0
        )
        
        return ChatResponse(
            response=fallback_response["content"],
            session_id=session.session_id,
            tokens_used=0,
            safety_check_passed=True
        )


@router.post("/chat/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get streaming response
    """
    # Rate limiting
    is_limited, _ = check_rate_limit(current_user.id)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {MAX_REQUESTS_PER_MINUTE} requests per minute"
        )
    
    # Safety check
    safety_checker = await get_safety_checker()
    safety_result = await safety_checker.comprehensive_check(
        message=request.message,
        user_id=str(current_user.id)
    )
    
    if not safety_result.is_safe:
        async def error_generator():
            yield f"data: {json.dumps({'chunk': safety_result.message, 'done': False})}\n\n"
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")
    
    # Get or create session
    session = await get_or_create_session(
        session_id=request.session_id,
        user_id=current_user.id,
        db=db,
        title=request.message[:50] if not request.session_id else None
    )
    
    # Save user message
    clean_message = safety_checker.redact_pii(request.message)
    await save_message(db, session.id, "user", clean_message)
    
    # Get AI Engine
    ai_engine = await get_ai_engine()
    skill_level_map = {
        "beginner": SkillLevel.BEGINNER,
        "intermediate": SkillLevel.INTERMEDIATE,
        "advanced": SkillLevel.ADVANCED
    }
    skill_level = skill_level_map.get(current_user.skill_level, SkillLevel.BEGINNER)
    
    async def stream_generator():
        full_response = ""
        try:
            response = await ai_engine.get_response(
                message=clean_message,
                session_id=session.session_id,
                user_id=current_user.id,
                skill_level=skill_level,
                stream=True
            )
            
            # Handle streaming response
            async for chunk in response:
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            
            # Add ethical disclaimer
            full_response = safety_checker.add_ethical_disclaimer(full_response)
            
            # Save assistant message
            await save_message(db, session.id, "assistant", full_response)
            
            yield f"data: {json.dumps({'chunk': '', 'done': True, 'full_response': full_response})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_msg = "⚠️ I'm having trouble generating a response. Please try again."
            yield f"data: {json.dumps({'chunk': error_msg, 'done': True})}\n\n"
    
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all chat sessions for current user"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    # Get message count for each session
    for session in sessions:
        count_result = await db.execute(
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == session.id)
        )
        session.message_count = count_result.scalar()
    
    return sessions


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=data.title or "New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get full conversation history for a session"""
    # Get session
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    messages.reverse()  # Oldest first
    
    # Get total count
    count_result = await db.execute(
        select(func.count(ChatMessage.id))
        .where(ChatMessage.session_id == session.id)
    )
    total_messages = count_result.scalar()
    
    return ChatHistoryResponse(
        session_id=session.session_id,
        messages=messages,
        total_messages=total_messages,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update session title"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if data.title:
        session.title = data.title
    if data.archived is not None:
        # Add archived field to model if needed
        pass
    
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/sessions/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_sessions_endpoint(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clean up sessions older than specified days (admin only)"""
    # Check if user is admin (you may want to add an is_admin field)
    # For now, only allow if user_id is 1 (first user)
    if current_user.id != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deleted_count = await cleanup_old_sessions(db, days)
    return {"deleted_sessions": deleted_count, "days_threshold": days}


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_chat_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat statistics for current user"""
    # Total sessions
    sessions_result = await db.execute(
        select(func.count(ChatSession.id))
        .where(ChatSession.user_id == current_user.id)
    )
    total_sessions = sessions_result.scalar()
    
    # Total messages
    messages_result = await db.execute(
        select(func.count(ChatMessage.id))
        .select_from(ChatMessage)
        .join(ChatSession)
        .where(ChatSession.user_id == current_user.id)
    )
    total_messages = messages_result.scalar()
    
    # Total tokens used
    tokens_result = await db.execute(
        select(func.sum(ChatMessage.tokens_used))
        .select_from(ChatMessage)
        .join(ChatSession)
        .where(ChatSession.user_id == current_user.id)
    )
    total_tokens = tokens_result.scalar() or 0
    
    # Last 7 days activity
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_result = await db.execute(
        select(func.count(ChatMessage.id))
        .select_from(ChatMessage)
        .join(ChatSession)
        .where(
            ChatSession.user_id == current_user.id,
            ChatMessage.created_at >= seven_days_ago
        )
    )
    recent_messages = recent_result.scalar() or 0
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "recent_messages_7d": recent_messages,
        "rate_limit": MAX_REQUESTS_PER_MINUTE
    }


# ============= WebSocket Endpoint =============

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat
    """
    # Authenticate user (custom auth for WebSocket)
    user = await get_current_user_ws(websocket, db)
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    await websocket.accept()
    await manager.connect(websocket, user.id)
    
    # Get or create session
    session = await get_or_create_session(session_id, user.id, db)
    
    # Send previous messages
    history = await get_conversation_history(db, session.id, limit=50)
    for msg in history:
        await websocket.send_json({
            "type": "history",
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat()
        })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                continue
            
            # Send typing indicator
            await websocket.send_json({"type": "typing", "is_typing": True})
            
            # Safety check
            safety_checker = await get_safety_checker()
            safety_result = await safety_checker.comprehensive_check(
                message=message,
                user_id=str(user.id)
            )
            
            if not safety_result.is_safe:
                await websocket.send_json({
                    "type": "error",
                    "content": safety_result.message
                })
                continue
            
            # Save user message
            clean_message = safety_checker.redact_pii(message)
            await save_message(db, session.id, "user", clean_message)
            
            # Echo user message
            await websocket.send_json({
                "type": "message",
                "role": "user",
                "content": clean_message
            })
            
            # Get AI response
            ai_engine = await get_ai_engine()
            skill_level_map = {
                "beginner": SkillLevel.BEGINNER,
                "intermediate": SkillLevel.INTERMEDIATE,
                "advanced": SkillLevel.ADVANCED
            }
            skill_level = skill_level_map.get(user.skill_level, SkillLevel.BEGINNER)
            
            full_response = ""
            
            try:
                response = await ai_engine.get_response(
                    message=clean_message,
                    session_id=session.session_id,
                    user_id=user.id,
                    skill_level=skill_level,
                    stream=True
                )
                
                # Stream response chunks
                async for chunk in response:
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })
                
                # Add disclaimer
                full_response = safety_checker.add_ethical_disclaimer(full_response)
                
                # Save assistant message
                await save_message(db, session.id, "assistant", full_response)
                
                # Send completion
                await websocket.send_json({
                    "type": "complete",
                    "content": full_response
                })
                
            except Exception as e:
                logger.error(f"WebSocket AI error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": "⚠️ I'm having trouble generating a response. Please try again."
                })
            
            # Remove typing indicator
            await websocket.send_json({"type": "typing", "is_typing": False})
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user.id)
        logger.info(f"User {user.id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket, user.id)
