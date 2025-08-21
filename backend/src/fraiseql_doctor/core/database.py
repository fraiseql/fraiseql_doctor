"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from fraiseql_doctor.core.config import get_settings


# Async database session (for async operations)
async def get_database_session() -> AsyncSession:
    """Get async database session."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


# Sync database session (for CLI operations)
def get_db_session() -> Session:
    """Get synchronous database session for CLI operations."""
    settings = get_settings()

    # Convert async URL to sync URL
    sync_url = settings.database_url.replace("+asyncpg", "")
    if "+asyncpg" not in settings.database_url:
        # If it was already sync, just use it
        sync_url = settings.database_url

    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Database configuration class for config management
class DatabaseConfig:
    """Database configuration helper."""

    def __init__(
        self,
        url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        self.url = url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle


def init_database():
    """Initialize database schema."""
    # This would run Alembic migrations
    # For now, just a placeholder
    print("Database initialization would run here")


def get_config():
    """Get configuration object."""
    settings = get_settings()

    # Create a configuration object that matches what the CLI expects
    class Config:
        def __init__(self):
            self.database = DatabaseConfig(url=settings.database_url)

    return Config()
