# Phase 1: TDD Foundation Setup
**Agent: Test-Driven Project Architect**

## Objective
Create a test-driven Python project foundation for "fraiseql_doctor" using modern tooling (uv, ruff) with comprehensive testing infrastructure established FIRST, ensuring every feature will be developed using RED-GREEN-REFACTOR methodology.

## 🔄 TDD Core Principle
**TESTS DRIVE DEVELOPMENT** - Every line of production code must be written to make a failing test pass.

## Phase 1 TDD Workflow

### Step 1: Test Infrastructure Foundation (RED Phase)
Set up testing framework and infrastructure before any application code.

#### 1.1 Core Test Configuration
```python
# tests/conftest.py - Created FIRST
"""Test configuration and shared fixtures."""
import pytest
import asyncio
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database URL - use real PostgreSQL for integration tests
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide database session with automatic rollback."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        transaction = await session.begin()
        yield session
        await transaction.rollback()
```

#### 1.2 Project Structure Test
```python
# tests/test_project_structure.py - Write FIRST to define requirements
"""Test that project structure meets requirements."""
import pytest
from pathlib import Path

def test_project_structure_exists():
    """Test that all required directories exist."""
    base_path = Path(__file__).parent.parent

    required_dirs = [
        "src/fraiseql_doctor",
        "src/fraiseql_doctor/cli",
        "src/fraiseql_doctor/core",
        "src/fraiseql_doctor/models",
        "src/fraiseql_doctor/services",
        "src/fraiseql_doctor/utils",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "docs",
        "scripts",
        "alembic"
    ]

    for dir_path in required_dirs:
        assert (base_path / dir_path).exists(), f"Directory {dir_path} must exist"

def test_configuration_files_exist():
    """Test that all configuration files exist."""
    base_path = Path(__file__).parent.parent

    required_files = [
        "pyproject.toml",
        "README.md",
        "Makefile",
        ".env.example",
        ".gitignore",
        ".pre-commit-config.yaml"
    ]

    for file_path in required_files:
        assert (base_path / file_path).exists(), f"File {file_path} must exist"

def test_package_structure():
    """Test that package structure is importable."""
    try:
        import fraiseql_doctor
        import fraiseql_doctor.core
        import fraiseql_doctor.models
        import fraiseql_doctor.services
        import fraiseql_doctor.cli
    except ImportError as e:
        pytest.fail(f"Package structure not properly configured: {e}")
```

### Step 2: Basic Functionality Tests (RED Phase)
Write failing tests that define core behavior BEFORE implementation.

#### 2.1 CLI Interface Tests
```python
# tests/test_cli_basic.py - Write FIRST
"""Test basic CLI functionality."""
import pytest
from typer.testing import CliRunner
from fraiseql_doctor.cli.main import app

def test_cli_app_exists():
    """Test that CLI app can be imported and instantiated."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "fraiseql-doctor" in result.stdout.lower()

def test_version_command():
    """Test version command works."""
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout

def test_subcommands_exist():
    """Test that required subcommands exist."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    required_commands = ["query", "endpoint", "health", "config"]
    for command in required_commands:
        assert command in result.stdout
```

#### 2.2 Database Connection Tests
```python
# tests/test_database_connection.py - Write FIRST
"""Test database connectivity and basic operations."""
import pytest
from fraiseql_doctor.core.database import get_database_session

async def test_database_connection(test_engine):
    """Test that database connection works."""
    async with test_engine.connect() as conn:
        result = await conn.execute("SELECT 1 as test_value")
        row = result.fetchone()
        assert row[0] == 1

async def test_database_session_creation(db_session):
    """Test that database sessions can be created."""
    assert db_session is not None
    # Session should support basic operations
    result = await db_session.execute("SELECT 1 as test_value")
    row = result.fetchone()
    assert row[0] == 1
```

### Step 3: Implementation (GREEN Phase)
Now implement minimal code to make tests pass.

#### 3.1 Project Structure Creation
```bash
# Create directory structure to pass structure tests
mkdir -p src/fraiseql_doctor/{cli,core,models,services,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p {docs,scripts,alembic}
touch src/fraiseql_doctor/__init__.py
touch src/fraiseql_doctor/{cli,core,models,services,utils}/__init__.py
```

#### 3.2 Basic CLI Implementation
```python
# src/fraiseql_doctor/cli/main.py - Minimal implementation
"""FraiseQL Doctor CLI application."""
import typer
from typing import Optional

app = typer.Typer(
    name="fraiseql-doctor",
    help="Health monitoring and query execution tool for FraiseQL/GraphQL endpoints"
)

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version")
):
    """FraiseQL Doctor main CLI."""
    if version:
        typer.echo("FraiseQL Doctor v0.1.0")
        raise typer.Exit()

# Placeholder subcommand groups
query_app = typer.Typer(name="query", help="Manage queries")
endpoint_app = typer.Typer(name="endpoint", help="Manage endpoints")
health_app = typer.Typer(name="health", help="Health monitoring")
config_app = typer.Typer(name="config", help="Configuration")

app.add_typer(query_app, name="query")
app.add_typer(endpoint_app, name="endpoint")
app.add_typer(health_app, name="health")
app.add_typer(config_app, name="config")

if __name__ == "__main__":
    app()
```

#### 3.3 Database Module
```python
# src/fraiseql_doctor/core/database.py - Minimal implementation
"""Database connection and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fraiseql_doctor.core.config import get_settings

async def get_database_session() -> AsyncSession:
    """Get database session."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
```

### Step 4: Configuration and Dependencies (GREEN Phase)

#### 4.1 pyproject.toml - TDD Enhanced
```toml
[project]
name = "fraiseql-doctor"
version = "0.1.0"
description = "Test-driven health monitoring and query execution tool for FraiseQL/GraphQL endpoints"
authors = [{name = "TDD Developer", email = "dev@example.com"}]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"

dependencies = [
    "typer[all]>=0.9.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary]>=3.1.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0",
    "aiohttp>=3.8.0",
    "rich>=13.0.0",
    "click>=8.0.0",
    "python-dotenv>=1.0.0",
    "alembic>=1.12.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0",
    "aioresponses>=0.7.4",  # For HTTP mocking
    "hypothesis>=6.82.0",   # Property-based testing
    "fakeredis>=2.18.0",    # Redis testing
]

[project.scripts]
fraiseql-doctor = "fraiseql_doctor.cli.main:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=85",
    "--strict-markers",
    "-v"
]
markers = [
    "integration: Integration tests",
    "performance: Performance tests",
    "slow: Slow running tests"
]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/conftest.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["ALL"]
ignore = [
    "D203", "D213",     # Docstring formatting
    "COM812", "ISC001", # Conflicts with formatter
    "S101",             # Allow assert in tests
]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101", "PLR2004", "SLF001", "D100", "D103"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### 4.2 Makefile - TDD Focused
```makefile
.PHONY: install dev test test-unit test-integration test-performance lint format clean build

# Development setup
install:
	uv sync

dev:
	uv sync --group dev

# Testing commands - Primary focus
test: test-unit test-integration
	@echo "All tests completed successfully!"

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-performance:
	uv run pytest tests/ -m performance -v

test-coverage:
	uv run pytest --cov=src --cov-report=html --cov-report=term

test-watch:
	uv run pytest-watch -- tests/

# TDD workflow helpers
tdd-cycle:
	@echo "🔴 RED: Write failing test"
	@echo "🟢 GREEN: Make test pass"
	@echo "🔵 REFACTOR: Improve code"

red:
	@echo "🔴 RED Phase: Write a failing test first!"
	uv run pytest tests/ -x -v

green:
	@echo "🟢 GREEN Phase: Make the test pass!"
	uv run pytest tests/ -x -v

refactor:
	@echo "🔵 REFACTOR Phase: Improve code while keeping tests green!"
	uv run pytest tests/ -v
	make lint
	make format

# Code quality
lint:
	uv run ruff check .
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

# Database operations
db-test-setup:
	@echo "Setting up test database..."
	createdb fraiseql_doctor_test || true
	uv run alembic upgrade head

db-test-reset:
	@echo "Resetting test database..."
	dropdb fraiseql_doctor_test || true
	createdb fraiseql_doctor_test
	uv run alembic upgrade head

# Project management
clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	uv build

run:
	uv run fraiseql-doctor

# Pre-commit hooks
pre-commit-install:
	uv run pre-commit install

pre-commit-run:
	uv run pre-commit run --all-files
```

### Step 5: REFACTOR Phase
Improve the foundation while keeping tests green.

#### 5.1 Enhanced Test Configuration
```python
# tests/conftest.py - Enhanced version
"""Enhanced test configuration with better fixtures."""
import pytest
import asyncio
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fraiseql_doctor.models.base import Base

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine with proper setup/teardown."""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test",
        echo=False,
        pool_pre_ping=True
    )

    # Create all tables for testing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide database session with transaction rollback."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        transaction = await session.begin()
        yield session
        await transaction.rollback()

@pytest.fixture
def temp_config_dir():
    """Provide temporary configuration directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
```

## TDD Success Criteria for Phase 1

### RED Phase Verification ✅
- [ ] All test files written before implementation code
- [ ] Tests fail initially (RED state confirmed)
- [ ] Test coverage targets defined

### GREEN Phase Verification ✅
- [ ] Minimal implementation makes all tests pass
- [ ] No over-engineering beyond test requirements
- [ ] All tests consistently pass

### REFACTOR Phase Verification ✅
- [ ] Code quality improved while tests remain green
- [ ] Performance optimizations applied
- [ ] Test coverage maintained or improved

### Foundation Quality Gates
- [ ] **Test Infrastructure**: Complete test setup with real database
- [ ] **Project Structure**: All directories and files exist per tests
- [ ] **CLI Basic**: Version and help commands work
- [ ] **Database**: Connection and session management functional
- [ ] **Dependencies**: All required packages properly configured
- [ ] **Development Workflow**: Make commands work for TDD cycle

## Handoff to Phase 2
With test-driven foundation complete, Phase 2 will continue TDD approach for database schema:

1. **Tests First**: Write failing tests for database models
2. **Schema Definition**: Implement models to pass tests
3. **Migration Tests**: Test Alembic migrations work correctly
4. **Performance Tests**: Database operation benchmarks

This TDD foundation ensures every subsequent phase builds on solid, tested ground with confidence that changes won't break existing functionality.
