# File: backend/api/chatbot/routes.py

import uuid
import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta

from config.security import get_current_user, get_current_user_ws
from api.chatbot.firebase_chat import FirebaseChatManager
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
chat_manager = FirebaseChatManager()

# ============= Rate Limiting =============
from collections import defaultdict
_rate_limit_tracker: dict = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 20

def check_rate_limit(user_uid: str) -> tuple[bool, int]:
    """Check if user has exceeded rate limit"""
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    
    _rate_limit_tracker[user_uid] = [
        ts for ts in _rate_limit_tracker[user_uid] 
        if ts > one_minute_ago
    ]
    
    request_count = len(_rate_limit_tracker[user_uid])
    is_limited = request_count >= MAX_REQUESTS_PER_MINUTE
    
    if not is_limited:
        _rate_limit_tracker[user_uid].append(now)
    
    return is_limited, request_count

# ============= WebSocket Connection Manager =============

class ConnectionManager:
    """Manage WebSocket connections for real-time interaction"""
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_uid: str):
        async with self._lock:
            if user_uid not in self.active_connections:
                self.active_connections[user_uid] = []
            self.active_connections[user_uid].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, user_uid: str):
        async with self._lock:
            if user_uid in self.active_connections:
                if websocket in self.active_connections[user_uid]:
                    self.active_connections[user_uid].remove(websocket)
                if not self.active_connections[user_uid]:
                    del self.active_connections[user_uid]
    
    async def send_message(self, user_uid: str, message: dict):
        if user_uid in self.active_connections:
            for connection in self.active_connections[user_uid]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message: {e}")

manager = ConnectionManager()

# ============= REST Endpoints =============

@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Send a message to the AI mentor and persist in Firestore"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_uid = current_user['uid']
    start_time = datetime.utcnow()
    
    # Rate limiting
    is_limited, _ = check_rate_limit(user_uid)
    if is_limited:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Safety Check
    safety_checker = await get_safety_checker()
    safety_result = await safety_checker.comprehensive_check(request.message, user_uid)
    if not safety_result.is_safe:
        return ChatResponse(
            response=safety_result.message,
            session_id=request.session_id or "",
            tokens_used=0,
            safety_check_passed=False,
            processing_time_ms=0
        )
    
    # Get or Create Session
    session_id = request.session_id
    if not session_id:
        session = await chat_manager.create_session(user_uid, title=request.message[:50])
        session_id = session['session_id']
    else:
        # Verify session exists and belongs to user
        session = await chat_manager.get_session(user_uid, session_id)
        if not session:
            session = await chat_manager.create_session(user_uid)
            session_id = session['session_id']
            
    # Save User Message
    clean_message = safety_checker.redact_pii(request.message)
    await chat_manager.add_message(user_uid, session_id, "user", clean_message)
    
    # Get AI Response
    ai_engine = await get_ai_engine()
    skill_level_map = {"beginner": SkillLevel.BEGINNER, "intermediate": SkillLevel.INTERMEDIATE, "advanced": SkillLevel.ADVANCED}
    skill_level = skill_level_map.get(current_user.get('skill_level', 'beginner'), SkillLevel.BEGINNER)
    
    try:
        ai_response = await ai_engine.get_response(
            message=clean_message,
            session_id=session_id,
            user_id=user_uid,
            skill_level=skill_level,
            stream=False
        )
        
        response_text = ai_response["content"]
        tokens_used = ai_response.get("tokens_used", 0)
        
        # Save Assistant Message
        await chat_manager.add_message(user_uid, session_id, "assistant", response_text, tokens_used)
        
        # Notify via WebSocket if connected
        await manager.send_message(user_uid, {
            "type": "new_message",
            "session_id": session_id,
            "message_preview": response_text[:100]
        })
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            tokens_used=tokens_used,
            safety_check_passed=True,
            processing_time_ms=ai_response.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        logger.error(f"AI Engine Error: {e}")
        fallback = "⚠️ I'm currently experiencing high demand. Please try again in a moment."
        await chat_manager.add_message(user_uid, session_id, "assistant", fallback)
        return ChatResponse(response=fallback, session_id=session_id, tokens_used=0)

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """Retrieve all chat sessions for the authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await chat_manager.get_sessions(current_user['uid'])

@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_session_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve full message history for a specific session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_uid = current_user['uid']
    session = await chat_manager.get_session(user_uid, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = await chat_manager.get_session_messages(user_uid, session_id)
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages),
        created_at=session.get('created_at', datetime.utcnow()),
        updated_at=session.get('updated_at', datetime.utcnow())
    )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete a chat session and its messages"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    await chat_manager.delete_session(current_user['uid'], session_id)

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """Real-time interaction via WebSockets with Firestore persistence"""
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    user_uid = user['uid']
    await websocket.accept()
    await manager.connect(websocket, user_uid)
    
    try:
        # Get session or create
        session = await chat_manager.get_session(user_uid, session_id)
        if not session:
            session = await chat_manager.create_session(user_uid, title="WebSocket Chat")
            session_id = session['session_id']
            
        # Send history
        history = await chat_manager.get_session_messages(user_uid, session_id, limit=30)
        for msg in history:
            await websocket.send_json({"type": "history", "role": msg['role'], "content": msg['content']})
            
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            if not message: continue
            
            # Save and echo user message
            await chat_manager.add_message(user_uid, session_id, "user", message)
            await websocket.send_json({"type": "message", "role": "user", "content": message})
            
            # Stream AI response
            ai_engine = await get_ai_engine()
            full_response = ""
            try:
                response_stream = await ai_engine.get_response(
                    message=message, session_id=session_id, user_id=user_uid, stream=True
                )
                async for chunk in response_stream:
                    full_response += chunk
                    await websocket.send_json({"type": "chunk", "content": chunk})
                
                await chat_manager.add_message(user_uid, session_id, "assistant", full_response)
                await websocket.send_json({"type": "complete", "content": full_response})
            except Exception as e:
                logger.error(f"WS AI Error: {e}")
                await websocket.send_json({"type": "error", "content": "AI connection failed"})
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, user_uid)
    except Exception as e:
        logger.error(f"WS Fatal: {e}")
        await manager.disconnect(websocket, user_uid)
