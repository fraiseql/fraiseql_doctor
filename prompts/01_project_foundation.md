# Phase 1: Project Foundation Setup
**Agent: Project Architect**

## Objective
Create a new Python project called "fraiseql_doctor" using modern tooling (uv, ruff) that will serve as a comprehensive health monitoring and query execution tool for FraiseQL/GraphQL endpoints.

## Requirements

### Core Technology Stack
- **Package Manager**: Use uv for dependency management (not poetry)
- **Linting/Formatting**: Set up ruff for linting and formatting with aggressive settings
- **Python Version**: Python 3.11+ support with modern type hints
- **CLI Framework**: Include basic CLI scaffolding with typer
- **Testing**: Set up testing framework with pytest
- **Database**: PostgreSQL support via SQLAlchemy

### Essential Dependencies
```toml
dependencies = [
    "typer[all]>=0.9.0",
    "sqlalchemy>=2.0.0",
    "psycopg[binary]>=3.1.0",
    "pydantic>=2.0.0",
    "requests>=2.31.0",
    "fraiseql>=0.1.0",  # If available
    "rich>=13.0.0",
    "click>=8.0.0",
    "python-dotenv>=1.0.0",
    "alembic>=1.12.0"
]

dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0"
]
```

### Project Structure
```
fraiseql_doctor/
├── src/
│   └── fraiseql_doctor/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── base.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── base.py
│       └── utils/
│           ├── __init__.py
│           └── logging.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── scripts/
├── alembic/
├── pyproject.toml
├── README.md
├── Makefile
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
└── docker-compose.yml
```

### Configuration Files

#### pyproject.toml Template
```toml
[project]
name = "fraiseql-doctor"
version = "0.1.0"
description = "Health monitoring and query execution tool for FraiseQL/GraphQL endpoints"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.scripts]
fraiseql-doctor = "fraiseql_doctor.cli.main:app"

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["ALL"]
ignore = [
    "D203", "D213",  # Docstring formatting
    "COM812", "ISC001",  # Conflicts with formatter
]

[tool.ruff.per-file-ignores]
"tests/*" = ["S101", "PLR2004", "SLF001"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
```

#### Makefile Template
```makefile
.PHONY: install dev test lint format clean build

install:
	uv sync

dev:
	uv sync --dev

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html

lint:
	uv run ruff check .
	uv run mypy src

format:
	uv run ruff format .
	uv run ruff check --fix .

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	uv build

run:
	uv run fraiseql-doctor

db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

db-migration:
	uv run alembic revision --autogenerate -m "$(message)"
```

### Initial CLI Structure
Create a basic typer application in `src/fraiseql_doctor/cli/main.py`:

```python
"""FraiseQL Doctor CLI application."""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="fraiseql-doctor",
    help="Health monitoring and query execution tool for FraiseQL/GraphQL endpoints",
    rich_markup_mode="rich",
)
console = Console()

@app.command()
def health() -> None:
    """Check health of configured FraiseQL endpoints."""
    console.print("[green]FraiseQL Doctor - Health Check[/green]")
    # Placeholder implementation
    
@app.command()
def query() -> None:
    """Execute stored FraiseQL queries."""
    console.print("[blue]FraiseQL Doctor - Query Execution[/blue]")
    # Placeholder implementation

@app.command()
def version() -> None:
    """Show version information."""
    console.print("FraiseQL Doctor v0.1.0")

if __name__ == "__main__":
    app()
```

### Quality Controls
1. Set up pre-commit hooks for ruff, mypy, and pytest
2. Configure GitHub Actions for CI/CD
3. Include comprehensive .gitignore for Python projects
4. Set up logging configuration with structured logging
5. Include environment variable management with python-dotenv

### Documentation Requirements
- Clear README with installation and usage instructions
- Contribution guidelines
- Code of conduct
- License file (MIT recommended)
- API documentation structure

### Success Criteria
- [x] Project structure created and organized
- [x] All configuration files in place and validated
- [x] Basic CLI commands functional
- [x] Dependencies installed and working
- [x] Testing framework set up
- [x] Linting and formatting configured
- [x] Database migration framework ready
- [x] Development workflow documented

### Handoff Notes for Next Phase
- Database models should be created in `src/fraiseql_doctor/models/`
- Use SQLAlchemy 2.0+ async patterns
- Follow PrintOptim naming conventions (tb_*, pk_*)
- Ensure all models inherit from a base model with common fields
- Include proper relationship definitions for FraiseQL-specific data