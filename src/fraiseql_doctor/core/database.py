"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fraiseql_doctor.core.config import get_settings


async def get_database_session() -> AsyncSession:
    """Get database session."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
