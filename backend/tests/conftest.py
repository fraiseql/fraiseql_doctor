"""Test configuration and shared fixtures."""

import pytest

# Import all database fixtures

# Configure pytest-asyncio to use function scope for event loops
pytestmark = pytest.mark.asyncio


# Ensure template database is set up before any tests
@pytest.fixture(scope="session", autouse=True)
def ensure_test_database(setup_test_database):
    """Automatically ensure test database is ready before running tests."""
    return setup_test_database
