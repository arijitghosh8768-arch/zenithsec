# File: backend/api/chatbot/firebase_chat.py
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from google.cloud.firestore import SERVER_TIMESTAMP
from config.firebase_admin_config import db

class FirebaseChatManager:
    """Manage chat sessions and messages in Firestore"""
    
    @staticmethod
    async def create_session(user_uid: str, title: str = "New Chat") -> Dict:
        """Create a new chat session in Firestore"""
        # User-centric session path
        session_ref = db.collection('users').document(user_uid).collection('sessions').document()
        
        session_data = {
            'session_id': session_ref.id,
            'title': title,
            'created_at': SERVER_TIMESTAMP,
            'updated_at': SERVER_TIMESTAMP,
            'message_count': 0,
            'user_uid': user_uid
        }
        
        session_ref.set(session_data)
        
        return {
            'id': session_ref.id,
            'session_id': session_ref.id,
            'title': title,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'message_count': 0
        }
    
    @staticmethod
    async def get_sessions(user_uid: str, limit: int = 50) -> List[Dict]:
        """Get all chat sessions for a user, ordered by last activity"""
        sessions_ref = db.collection('users').document(user_uid).collection('sessions')
        sessions = sessions_ref.order_by('updated_at', direction='DESC').limit(limit).stream()
        
        result = []
        for doc in sessions:
            data = doc.to_dict()
            # Convert Firestore timestamp to Python datetime if needed
            result.append({
                'id': doc.id,
                'session_id': doc.id,
                'title': data.get('title', 'New Chat'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'message_count': data.get('message_count', 0)
            })
        
        return result

    @staticmethod
    async def get_session(user_uid: str, session_id: str) -> Optional[Dict]:
        """Get a specific session from Firestore"""
        doc_ref = db.collection('users').document(user_uid).collection('sessions').document(session_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    
    @staticmethod
    async def add_message(user_uid: str, session_id: str, role: str, content: str, tokens_used: int = 0) -> Dict:
        """Add a message to a session and update session metadata"""
        # Add message to 'messages' subcollection
        session_doc_ref = db.collection('users').document(user_uid).collection('sessions').document(session_id)
        messages_ref = session_doc_ref.collection('messages').document()
        
        message_data = {
            'message_id': messages_ref.id,
            'role': role,
            'content': content,
            'tokens_used': tokens_used,
            'created_at': SERVER_TIMESTAMP
        }
        
        messages_ref.set(message_data)
        
        # Update session timestamp and message count increment
        from firebase_admin import firestore
        session_doc_ref.update({
            'updated_at': SERVER_TIMESTAMP,
            'message_count': firestore.Increment(1)
        })
        
        return {
            'message_id': messages_ref.id,
            'role': role,
            'content': content,
            'created_at': datetime.utcnow()
        }
    
    @staticmethod
    async def get_session_messages(user_uid: str, session_id: str, limit: int = 50) -> List[Dict]:
        """Get history for a specific chat session"""
        messages_ref = db.collection('users').document(user_uid).collection('sessions').document(session_id).collection('messages')
        messages = messages_ref.order_by('created_at').limit(limit).stream()
        
        result = []
        for doc in messages:
            data = doc.to_dict()
            result.append({
                'id': doc.id,
                'role': data.get('role'),
                'content': data.get('content'),
                'tokens_used': data.get('tokens_used', 0),
                'created_at': data.get('created_at')
            })
        
        return result
    
    @staticmethod
    async def delete_session(user_uid: str, session_id: str):
        """Delete a session and its associated messages"""
        session_ref = db.collection('users').document(user_uid).collection('sessions').document(session_id)
        
        # Firestore doesn't automatically delete subcollections. Delete messages first.
        messages = session_ref.collection('messages').stream()
        for msg in messages:
            msg.reference.delete()
        
        # Delete session document
        session_ref.delete()
        
        return True

    @staticmethod
    async def update_session(user_uid: str, session_id: str, title: str):
        """Update session metadata (like title)"""
        session_ref = db.collection('users').document(user_uid).collection('sessions').document(session_id)
        session_ref.update({
            'title': title,
            'updated_at': SERVER_TIMESTAMP
        })
        return True
