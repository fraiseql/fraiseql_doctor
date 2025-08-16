"""Configuration management for FraiseQL Doctor."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(default="postgresql://localhost/fraiseql_doctor")
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    echo: bool = Field(default=False)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class DefaultsConfig(BaseModel):
    """Default settings."""

    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    health_check_interval: int = Field(default=300)


class Settings(BaseSettings):
    """Application settings."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)

    class Config:
        env_prefix = "FRAISEQL_DOCTOR_"
        case_sensitive = False


def load_config_from_file(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        # Default config locations
        config_locations = [
            Path.home() / ".fraiseql-doctor" / "config.yaml",
            Path.cwd() / "config.yaml",
            Path("/etc/fraiseql-doctor/config.yaml"),
        ]

        for location in config_locations:
            if location.exists():
                config_path = location
                break
        else:
            return {}

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def get_settings(config_file: Path | None = None) -> Settings:
    """Get application settings."""
    # Load from file first
    file_config = load_config_from_file(config_file)

    # Create settings with file config as defaults
    return Settings(**file_config)
