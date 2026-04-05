# File: backend/config/firebase_admin_config.py
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase_admin():
    """Initialize Firebase Admin SDK for backend"""
    try:
        # Check if already initialized
        if firebase_admin._apps:
            return firebase_admin.get_app()
        
        # Get service account credentials from environment
        firebase_credentials = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if firebase_credentials:
            # Parse the JSON credentials
            try:
                cred_dict = json.loads(firebase_credentials)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                # Fallback: handles case where quotes might be missing
                import ast
                cred_dict = ast.literal_eval(firebase_credentials)
                cred = credentials.Certificate(cred_dict)
        else:
            # For local development, use default credentials or look for local file
            if os.path.exists("serviceAccountKey.json"):
                cred = credentials.Certificate("serviceAccountKey.json")
            else:
                cred = credentials.ApplicationDefault()
        
        app = firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized successfully")
        return app
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        # Don't raise here in dev to allow server to start, but in prod it should be critical
        return None

# Initialize Firebase
initialize_firebase_admin()

# Get clients
db = firestore.client()
auth_client = auth

__all__ = ['db', 'auth_client']
