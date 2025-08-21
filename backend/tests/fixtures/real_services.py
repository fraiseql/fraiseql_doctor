"""Real service implementations for testing instead of mocks."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import uuid4

from fraiseql_doctor.core.fraiseql_client import GraphQLExecutionError, NetworkError
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.complexity import QueryComplexityAnalyzer


class TestGraphQLClient:
    """Lightweight test GraphQL client - predictable responses without external dependencies."""

    def __init__(self, endpoint: Optional[Endpoint] = None):
        self.endpoint = endpoint
        self.call_count = 0
        self.should_fail = False
        self.custom_response = None
        self.failure_pattern = None
        self.random_failures = False
        self.failure_rate = 0.1
        self.realistic_timing = False
        self.default_response = None

    async def execute_query(
        self, query: str, variables: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Execute GraphQL query with predictable test responses."""
        self.call_count += 1
        variables = variables or {}

        # Handle failure scenarios
        if self.should_fail:
            if "network" in query.lower():
                raise NetworkError("Test network error")
            elif "error" in query.lower() or "fail" in query.lower():
                raise GraphQLExecutionError("Test GraphQL error")
            elif "poison" in query.lower():
                raise Exception("Poison query executed")

        # Handle pattern-based failures
        if self.failure_pattern and self.failure_pattern in query.lower():
            raise GraphQLExecutionError(f"Test failure for pattern: {self.failure_pattern}")

        # Handle random failures
        if self.random_failures:
            import secrets

            # Use cryptographically secure random for test failures
            secure_random = secrets.SystemRandom()
            if secure_random.random() < self.failure_rate:
                raise Exception("Random execution failure")

        # Realistic timing simulation
        if self.realistic_timing:
            import asyncio

            query_length = len(query)
            base_time = 0.1
            complexity_multiplier = query_length / 1000
            execution_time = base_time + complexity_multiplier
            await asyncio.sleep(min(execution_time, 2.0))

        # Return default response if set
        if self.default_response:
            return self.default_response.copy()

        # Return custom response if set
        if self.custom_response:
            return self.custom_response.copy()

        # Generate predictable response based on query content
        if "users" in query.lower():
            return {
                "data": {
                    "users": [
                        {"id": "1", "name": "Test User 1", "email": "user1@test.com"},
                        {"id": "2", "name": "Test User 2", "email": "user2@test.com"},
                    ]
                },
                "_complexity_score": 5.2,
                "_execution_time": 0.15,
            }
        elif "dashboard" in query.lower():
            return {
                "data": {
                    "dashboard": {
                        "stats": {"totalUsers": 100, "activeUsers": 80, "revenue": 5000},
                        "recentActivity": [],
                        "charts": {"userGrowth": [1, 2, 3], "revenueByMonth": [100, 200, 300]},
                    }
                },
                "_complexity_score": 15.8,
                "_execution_time": 0.45,
            }
        else:
            # Default response
            return {
                "data": {"test": "result", "timestamp": datetime.now(UTC).isoformat()},
                "_complexity_score": 3.0,
                "_execution_time": 0.1,
            }

    def set_failure_mode(self, should_fail: bool = True):
        """Enable/disable failure mode for testing error scenarios."""
        self.should_fail = should_fail

    def set_custom_response(self, response: dict[str, Any]):
        """Set a custom response for specific test scenarios."""
        self.custom_response = response

    def set_default_response(self, response: dict[str, Any]):
        """Set a default response for all queries."""
        self.default_response = response

    def set_failure_pattern(self, pattern: str):
        """Set a pattern that triggers failures when found in queries."""
        self.failure_pattern = pattern

    def set_random_failures(self, enable: bool = True):
        """Enable random failures for stress testing."""
        self.random_failures = enable

    def set_failure_rate(self, rate: float):
        """Set the rate of random failures (0.0 to 1.0)."""
        self.failure_rate = max(0.0, min(1.0, rate))

    def set_realistic_timing(self, enable: bool = True):
        """Enable realistic timing simulation based on query complexity."""
        self.realistic_timing = enable


class TestComplexityAnalyzer(QueryComplexityAnalyzer):
    """Enhanced complexity analyzer with predictable test results."""

    def __init__(self):
        super().__init__()
        self.should_fail = False
        self.custom_score = None

    async def analyze_query(self, query: str, variables: Optional[dict[str, Any]] = None):
        """Analyze query complexity with predictable test results."""
        if self.should_fail:
            if "invalid" in query.lower():
                raise ValueError("Invalid GraphQL syntax")
            elif "corrupted" in query.lower():
                raise ValueError("Corrupted query content")

        if self.custom_score is not None:
            score = self.custom_score
        else:
            # Predictable scoring based on query content
            if "complex" in query.lower() or "dashboard" in query.lower():
                score = 15.5
            elif len(query) > 1000:
                score = min(50.0, len(query) / 100.0)  # Scale with length
            elif query.count("{") > 3:  # Nested queries
                score = query.count("{") * 2.5
            else:
                score = 3.0

        @dataclass
        class AnalysisResult:
            complexity_score: float
            estimated_execution_time: float
            field_count: int
            depth: int

        return AnalysisResult(
            complexity_score=score,
            estimated_execution_time=score * 0.1,  # 100ms per complexity point
            field_count=max(1, query.count(" ")),
            depth=max(1, query.count("{")),
        )

    def set_failure_mode(self, should_fail: bool = True):
        """Enable/disable failure mode for testing error scenarios."""
        self.should_fail = should_fail

    def set_custom_score(self, score: float):
        """Set custom complexity score for specific tests."""
        self.custom_score = score


class TestDatabaseSession:
    """Lightweight test database session that tracks operations without real DB."""

    def __init__(self):
        self.objects = []
        self.committed = False
        self.should_fail = False
        self.call_count = 0
        self.results = []
        self.custom_error = None

    def add(self, obj):
        """Add object to session."""
        self.objects.append(obj)

    async def commit(self):
        """Commit transaction."""
        self.call_count += 1
        if self.should_fail:
            if self.custom_error:
                raise self.custom_error
            else:
                raise Exception("Database connection lost")
        self.committed = True

    async def execute(self, query: str, params: Optional[list] = None):
        """Execute query and return test results."""
        self.call_count += 1
        if self.should_fail:
            if self.custom_error:
                raise self.custom_error
            else:
                raise Exception("Database connection lost")
        return self.results

    async def get(self, model_class, primary_key):
        """Get object by primary key."""
        self.call_count += 1
        if self.should_fail:
            if self.custom_error:
                raise self.custom_error
            else:
                raise Exception("Database connection lost")

        # Return test object if requested
        if hasattr(model_class, "from_dict"):
            # Provide appropriate test data based on model type
            base_data = {
                "id": primary_key,
                "name": f"Test {model_class.__name__}",
                "created_by": "test-user",
            }

            # Add model-specific fields
            if "Endpoint" in model_class.__name__:
                base_data.update(
                    {
                        "pk_endpoint": primary_key,
                        "url": "https://api.test.com/graphql",
                        "auth_type": "bearer",
                        "auth_config": {"token": "test-token"},
                    }
                )
            elif "QueryCollection" in model_class.__name__:
                base_data.update(
                    {
                        "pk_query_collection": primary_key,
                        "description": "Test collection description",
                        "tags": {},
                        "collection_metadata": {},
                    }
                )
            elif "Query" in model_class.__name__:
                base_data.update(
                    {
                        "pk_query": primary_key,
                        "query_text": "query { test }",
                        "variables": {},
                        "query_metadata": {},
                    }
                )

            return model_class.from_dict(base_data)
        return None

    async def delete(self, obj):
        """Delete object."""
        if obj in self.objects:
            self.objects.remove(obj)

    def set_failure_mode(self, should_fail: bool = True):
        """Enable/disable failure mode."""
        self.should_fail = should_fail

    def set_results(self, results: list):
        """Set results to return from execute()."""
        self.results = results

    def set_custom_error(self, error: Exception):
        """Set a custom error to raise during database operations."""
        self.custom_error = error
        self.should_fail = True


def create_test_client_factory():
    """Create a client factory that returns test clients."""

    def factory(endpoint: Endpoint) -> TestGraphQLClient:
        return TestGraphQLClient(endpoint)

    return factory


def create_failing_client_factory():
    """Create a client factory that returns clients in failure mode."""

    def factory(endpoint: Endpoint) -> TestGraphQLClient:
        client = TestGraphQLClient(endpoint)
        client.set_failure_mode(True)
        return client

    return factory


async def create_test_endpoint() -> Endpoint:
    """Create a test endpoint for testing."""
    return Endpoint.from_dict(
        {
            "pk_endpoint": uuid4(),
            "name": "Test GraphQL Endpoint",
            "url": "https://api.test.com/graphql",
            "auth_type": "bearer",
            "auth_config": {"token": "test-token"},
            "timeout_seconds": 30,
            "max_retries": 3,
            "is_active": True,
        }
    )
