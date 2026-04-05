# File: backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure PORT environment variable is used
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ZenithSec API", 
    version="1.1.0",
    description="Advanced Cybersecurity AI Platform - Firebase Edition"
)

# CORS middleware for cross-origin production requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to zenithsec.vercel.app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ZenithSec API landing page with status report."""
    return {
        "name": "ZenithSec API",
        "status": "healthy",
        "provider": "Firebase Cloud Native",
        "version": "1.1.0"
    }

@app.get("/health")
@app.get("/api/health")
async def health():
    """Public health check endpoint for Render/Vercel connectivity."""
    from datetime import datetime
    return {
        "status": "ok", 
        "architecture": "Firestore-v1",
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Module Routers ---

# Import and include Firebase-native routers
try:
    from api.auth.routes import router as auth_router
    app.include_router(auth_router)
    logger.info("✓ Firebase Auth router loaded")
except Exception as e:
    logger.error(f"✗ Auth router load error: {e}")

try:
    from api.chatbot.routes import router as chatbot_router
    app.include_router(chatbot_router)
    logger.info("✓ Firestore Chatbot router loaded")
except Exception as e:
    logger.error(f"✗ Chatbot router load error: {e}")

try:
    from api.learning_hub.routes import router as learning_router
    app.include_router(learning_router)
    logger.info("✓ Learning Hub router loaded")
except Exception as e:
    logger.error(f"✗ Learning Hub load error: {e}")

try:
    from api.portfolio.routes import router as portfolio_router
    app.include_router(portfolio_router)
    logger.info("✓ Portfolio router loaded")
except Exception as e:
    logger.error(f"✗ Portfolio load error: {e}")

try:
    from api.analytics.routes import router as analytics_router
    app.include_router(analytics_router)
    logger.info("✓ Analytics router loaded")
except Exception as e:
    logger.error(f"✗ Analytics load error: {e}")

try:
    from api.code_vault.routes import router as codevault_router
    app.include_router(codevault_router)
    logger.info("✓ Code Vault router loaded")
except Exception as e:
    logger.error(f"✗ Code Vault load error: {e}")

try:
    from api.certificates.routes import router as cert_router
    app.include_router(cert_router)
    logger.info("✓ Certificates router loaded")
except Exception as e:
    logger.error(f"✗ Certificates load error: {e}")

logger.info("✅ ZenithSec Backend (Firebase) ready!")

if __name__ == "__main__":
    import uvicorn
    # Start the server on the correct port for Render
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
