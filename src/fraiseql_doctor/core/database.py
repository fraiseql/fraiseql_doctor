"""Database utilities and session management."""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings


class DatabaseManager:
    """Database manager for FraiseQL Doctor."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._async_engine = None
        self._session_factory = None
        self._async_session_factory = None

    @property
    def engine(self):
        """Get synchronous database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.database.url,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                echo=self.settings.database.echo,
            )
        return self._engine

    @property
    def async_engine(self):
        """Get asynchronous database engine."""
        if self._async_engine is None:
            # Convert PostgreSQL URL to async version
            async_url = self.settings.database.url.replace("postgresql://", "postgresql+asyncpg://")
            self._async_engine = create_async_engine(
                async_url,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                echo=self.settings.database.echo,
            )
        return self._async_engine

    @property
    def session_factory(self):
        """Get synchronous session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    @property
    def async_session_factory(self):
        """Get asynchronous session factory."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
            )
        return self._async_session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session."""
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def create_tables(self) -> None:
        """Create all database tables."""
        from fraiseql_doctor.models import Base
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        from fraiseql_doctor.models import Base
        Base.metadata.drop_all(bind=self.engine)

    async def create_tables_async(self) -> None:
        """Create all database tables asynchronously."""
        from fraiseql_doctor.models import Base
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables_async(self) -> None:
        """Drop all database tables asynchronously."""
        from fraiseql_doctor.models import Base
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def close(self) -> None:
        """Close database connections."""
        if self._engine:
            self._engine.dispose()
        if self._async_engine:
            # AsyncEngine needs to be closed in an async context
            # This should be called from an async function
            pass

    async def close_async(self) -> None:
        """Close database connections asynchronously."""
        if self._async_engine:
            await self._async_engine.dispose()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager(settings: Settings | None = None) -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        if settings is None:
            from .config import get_settings
            settings = get_settings()
        _db_manager = DatabaseManager(settings)
    return _db_manager


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    db_manager = get_database_manager()
    async with db_manager.get_async_session() as session:
        yield session