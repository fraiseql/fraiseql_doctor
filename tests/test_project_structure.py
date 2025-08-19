"""Test that project structure meets requirements."""

from pathlib import Path

import pytest


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
        "alembic",
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
        ".pre-commit-config.yaml",
    ]

    for file_path in required_files:
        assert (base_path / file_path).exists(), f"File {file_path} must exist"


def test_package_structure():
    """Test that package structure is importable."""
    try:
        import fraiseql_doctor
        import fraiseql_doctor.cli
        import fraiseql_doctor.core
        import fraiseql_doctor.models
        import fraiseql_doctor.services
    except ImportError as e:
        pytest.fail(f"Package structure not properly configured: {e}")
