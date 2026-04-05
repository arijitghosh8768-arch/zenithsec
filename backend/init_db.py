# File: backend/init_db.py

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from models.user import User
from models.learning import ChatSession, ChatMessage, Course, Lesson, LearningProgress, Portfolio, Project
from models.repository import Repository, File, Commit
from models.certificate import Certificate, Verification
from config.database import Base
from config.settings import settings

async def init_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Dropping existing tables and recreating then to ensure everything aligns with our new models
        # Commented: In a production or persistent dev env you wouldn't necessarily want this.
        # However, to clear out potential migration/schema issues, this is safest for now.
        print("Cleaning up database tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
