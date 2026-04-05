# File: backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Ensure PORT environment variable is used
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ZenithSec API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ZenithSec API is running", "status": "healthy"}

@app.get("/health")
async def render_health():
    """Reserved health check for Render/Vercel"""
    return {"status": "ok"}

@app.get("/api/health", tags=["Health"])
async def health():
    """Public health check endpoint (no auth required)"""
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Import routers
try:
    from api.auth.routes import router as auth_router
    app.include_router(auth_router)
    logger.info("✓ Auth router loaded")
except Exception as e:
    logger.error(f"✗ Auth router failed: {e}")

try:
    from api.chatbot.routes import router as chatbot_router
    app.include_router(chatbot_router)
    logger.info("✓ Chatbot router loaded")
except Exception as e:
    logger.error(f"✗ Chatbot router failed: {e}")

logger.info("✅ Server ready!")

if __name__ == "__main__":
    import uvicorn
    # Use string reference for reload capability and ensure correct port for Render
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
