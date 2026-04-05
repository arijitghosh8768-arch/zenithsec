# File: backend/config/settings.py

import os
from dotenv import load_dotenv

# Load .env file only in development
if not os.getenv("RENDER"):
    load_dotenv()

class Settings:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    
    # AI APIs
    GROQ_API_KEYS = [
        os.getenv("GROQ_API_KEY_PRIMARY", ""),
        os.getenv("GROQ_API_KEY_BACKUP", ""),
        os.getenv("GROQ_API_KEY_3", "")
    ]
    GROQ_API_KEY = GROQ_API_KEYS[0] # For backward compatibility
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    PROJECT_NAME = "ZenithSec"
    VERSION = "1.0.0"
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    
    # JWT Settings
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    # Firebase Settings
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "zenithsec-52df5")

    # Environment
    IS_PRODUCTION = bool(os.getenv("RENDER", False))

settings = Settings()
