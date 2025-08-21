"""Database integration for FastAPI."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fraiseql_doctor.core.config import get_settings


# Global async engine and session maker
_async_engine = None
_async_session_maker = None


def get_async_engine():
    """Get or create async database engine."""
    global _async_engine
    
    if _async_engine is None:
        settings = get_settings()
        # Convert sync URL to async URL if needed
        async_url = settings.database_url
        if 'postgresql://' in async_url and '+asyncpg' not in async_url:
            async_url = async_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        _async_engine = create_async_engine(
            async_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=20,
            max_overflow=30,
        )
    
    return _async_engine


def get_async_session_maker():
    """Get or create async session maker."""
    global _async_session_maker
    
    if _async_session_maker is None:
        engine = get_async_engine()
        _async_session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    return _async_session_maker


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session for FastAPI."""
    session_maker = get_async_session_maker()
    
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()