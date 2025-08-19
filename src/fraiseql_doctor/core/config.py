"""Configuration management for FraiseQL Doctor."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = "postgresql+asyncpg://fraiseql:password@localhost/fraiseql_doctor"
    test_database_url: str = "postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test"
    debug: bool = False
    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
