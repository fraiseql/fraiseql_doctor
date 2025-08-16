# Phase 6: Testing & Quality Assurance
**Agent: QA Engineer**

## Objective
Implement a comprehensive testing suite that ensures reliability, performance, and correctness of the FraiseQL Doctor system across all components with high coverage and robust error scenarios.

## Requirements

### Testing Architecture

#### 1. Test Configuration and Fixtures
```python
"""Test configuration and shared fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
import tempfile
from pathlib import Path

from fraiseql_doctor.models.base import Base
from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.core.config import Settings


# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
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
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_query(db_session: AsyncSession) -> Query:
    """Create a sample query for testing."""
    query = Query(
        pk_query=uuid4(),
        name="test-query",
        description="Test GraphQL query",
        query_text="""
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    name
                    email
                }
            }
        """,
        variables={"id": "123"},
        tags=["test", "user"],
        expected_complexity_score=50,
        created_by="test-user"
    )
    
    db_session.add(query)
    await db_session.commit()
    await db_session.refresh(query)
    
    return query


@pytest.fixture
async def sample_endpoint(db_session: AsyncSession) -> Endpoint:
    """Create a sample endpoint for testing."""
    endpoint = Endpoint(
        pk_endpoint=uuid4(),
        name="test-endpoint",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "test-token"},
        headers={"User-Agent": "fraiseql-doctor-test"},
        timeout_seconds=30,
        max_retries=3,
        retry_delay_seconds=1
    )
    
    db_session.add(endpoint)
    await db_session.commit()
    await db_session.refresh(endpoint)
    
    return endpoint


@pytest.fixture
def mock_graphql_server():
    """Mock GraphQL server for testing."""
    import aioresponses
    
    with aioresponses.aioresponses() as m:
        # Mock successful response
        m.post(
            "https://api.example.com/graphql",
            payload={
                "data": {
                    "user": {
                        "id": "123",
                        "name": "Test User",
                        "email": "test@example.com"
                    }
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        yield m


@pytest.fixture
def temp_config_file():
    """Create temporary configuration file."""
    config_content = """
database:
  url: "postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test"
  pool_size: 5

logging:
  level: "DEBUG"
  
defaults:
  timeout_seconds: 30
  max_retries: 3
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        yield Path(f.name)
        
        # Cleanup
        Path(f.name).unlink()
```

#### 2. Unit Tests for Core Services
```python
"""Unit tests for query service."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from fraiseql_doctor.services.query import QueryService
from fraiseql_doctor.services.validation import QueryValidator, ValidationResult
from fraiseql_doctor.schemas.query import QueryCreate, QueryUpdate
from fraiseql_doctor.core.exceptions import (
    QueryNotFoundError,
    QueryValidationError,
    DuplicateQueryError
)


class TestQueryService:
    """Test suite for QueryService."""
    
    @pytest.fixture
    def mock_validator(self):
        """Mock query validator."""
        validator = Mock(spec=QueryValidator)
        validator.validate_query = AsyncMock(return_value=ValidationResult(
            is_valid=True,
            complexity_score=50,
            errors=[]
        ))
        return validator
    
    @pytest.fixture
    def query_service(self, db_session, mock_validator):
        """Create query service with mocked dependencies."""
        return QueryService(db_session, mock_validator)
    
    async def test_create_query_success(self, query_service, mock_validator):
        """Test successful query creation."""
        query_data = QueryCreate(
            name="test-query",
            description="Test query",
            query_text="query { user { id name } }",
            variables={},
            tags=["test"],
            created_by="test-user"
        )
        
        result = await query_service.create_query(query_data)
        
        assert result.name == "test-query"
        assert result.description == "Test query"
        assert result.is_active is True
        assert result.expected_complexity_score == 50
        mock_validator.validate_query.assert_called_once()
    
    async def test_create_query_validation_error(self, query_service, mock_validator):
        """Test query creation with validation error."""
        mock_validator.validate_query.return_value = ValidationResult(
            is_valid=False,
            complexity_score=None,
            errors=["Invalid syntax"]
        )
        
        query_data = QueryCreate(
            name="invalid-query",
            query_text="invalid graphql",
            created_by="test-user"
        )
        
        with pytest.raises(QueryValidationError) as exc_info:
            await query_service.create_query(query_data)
        
        assert "Query validation failed" in str(exc_info.value)
    
    async def test_create_duplicate_query(self, query_service, sample_query):
        """Test creating query with duplicate name."""
        query_data = QueryCreate(
            name=sample_query.name,  # Use existing name
            query_text="query { user { id } }",
            created_by="test-user"
        )
        
        with pytest.raises(DuplicateQueryError):
            await query_service.create_query(query_data)
    
    async def test_get_query_success(self, query_service, sample_query):
        """Test successful query retrieval."""
        result = await query_service.get_query(sample_query.pk_query)
        
        assert result.pk_query == sample_query.pk_query
        assert result.name == sample_query.name
        assert result.query_text == sample_query.query_text
    
    async def test_get_query_not_found(self, query_service):
        """Test query retrieval with non-existent ID."""
        non_existent_id = uuid4()
        
        with pytest.raises(QueryNotFoundError):
            await query_service.get_query(non_existent_id)
    
    async def test_list_queries_with_filters(self, query_service, sample_query):
        """Test query listing with various filters."""
        # Test tag filter
        result = await query_service.list_queries(tags=["test"])
        assert len(result) == 1
        assert result[0].pk_query == sample_query.pk_query
        
        # Test non-matching tag
        result = await query_service.list_queries(tags=["nonexistent"])
        assert len(result) == 0
        
        # Test created_by filter
        result = await query_service.list_queries(created_by="test-user")
        assert len(result) == 1
        
        # Test is_active filter
        result = await query_service.list_queries(is_active=True)
        assert len(result) == 1
    
    async def test_update_query_success(self, query_service, sample_query, mock_validator):
        """Test successful query update."""
        update_data = QueryUpdate(
            name="updated-query",
            description="Updated description"
        )
        
        result = await query_service.update_query(sample_query.pk_query, update_data)
        
        assert result.name == "updated-query"
        assert result.description == "Updated description"
        assert result.pk_query == sample_query.pk_query
    
    async def test_update_query_with_revalidation(self, query_service, sample_query, mock_validator):
        """Test query update that triggers revalidation."""
        update_data = QueryUpdate(
            query_text="query { updatedUser { id name email } }"
        )
        
        result = await query_service.update_query(sample_query.pk_query, update_data)
        
        assert result.query_text == update_data.query_text
        mock_validator.validate_query.assert_called()
    
    async def test_delete_query_success(self, query_service, sample_query):
        """Test successful query deletion."""
        result = await query_service.delete_query(sample_query.pk_query)
        
        assert result is True
        
        # Verify query is deleted
        with pytest.raises(QueryNotFoundError):
            await query_service.get_query(sample_query.pk_query)
    
    async def test_delete_query_not_found(self, query_service):
        """Test deletion of non-existent query."""
        non_existent_id = uuid4()
        
        with pytest.raises(QueryNotFoundError):
            await query_service.delete_query(non_existent_id)


class TestExecutionService:
    """Test suite for ExecutionService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Mock client factory."""
        def factory(endpoint):
            client = AsyncMock()
            client.execute_query = AsyncMock()
            return client
        return factory
    
    @pytest.fixture
    def mock_metrics(self):
        """Mock metrics collector."""
        metrics = Mock()
        metrics.record_query = Mock()
        return metrics
    
    @pytest.fixture
    def execution_service(self, db_session, mock_client_factory, mock_metrics):
        """Create execution service with mocked dependencies."""
        from fraiseql_doctor.services.execution import ExecutionService
        return ExecutionService(db_session, mock_client_factory, mock_metrics)
    
    async def test_execute_query_success(
        self,
        execution_service,
        sample_query,
        sample_endpoint,
        mock_client_factory,
        mock_metrics
    ):
        """Test successful query execution."""
        from fraiseql_doctor.services.fraiseql_client import GraphQLResponse
        
        # Mock successful response
        mock_response = GraphQLResponse(
            data={"user": {"id": "123", "name": "Test User"}},
            errors=None,
            response_time_ms=100,
            complexity_score=50
        )
        
        mock_client = mock_client_factory(sample_endpoint)
        mock_client.execute_query.return_value = mock_response
        
        result = await execution_service.execute_query(
            query_id=sample_query.pk_query,
            endpoint_id=sample_endpoint.pk_endpoint
        )
        
        assert result["status"] == "success"
        assert result["response_time_ms"] == 100
        assert result["data"] == {"user": {"id": "123", "name": "Test User"}}
        assert result["complexity_score"] == 50
        
        mock_metrics.record_query.assert_called_once()
    
    async def test_execute_query_with_errors(
        self,
        execution_service,
        sample_query,
        sample_endpoint,
        mock_client_factory
    ):
        """Test query execution with GraphQL errors."""
        from fraiseql_doctor.services.fraiseql_client import GraphQLResponse
        
        mock_response = GraphQLResponse(
            data=None,
            errors=[{"message": "Field 'user' not found"}],
            response_time_ms=50,
            complexity_score=None
        )
        
        mock_client = mock_client_factory(sample_endpoint)
        mock_client.execute_query.return_value = mock_response
        
        result = await execution_service.execute_query(
            query_id=sample_query.pk_query,
            endpoint_id=sample_endpoint.pk_endpoint
        )
        
        assert result["status"] == "error"
        assert "Field 'user' not found" in result["errors"][0]["message"]
    
    async def test_execute_batch_queries(
        self,
        execution_service,
        sample_query,
        sample_endpoint,
        mock_client_factory
    ):
        """Test batch query execution."""
        from fraiseql_doctor.services.fraiseql_client import GraphQLResponse
        
        mock_response = GraphQLResponse(
            data={"user": {"id": "123"}},
            errors=None,
            response_time_ms=75
        )
        
        mock_client = mock_client_factory(sample_endpoint)
        mock_client.execute_query.return_value = mock_response
        
        executions = [
            {
                "query_id": sample_query.pk_query,
                "endpoint_id": sample_endpoint.pk_endpoint
            },
            {
                "query_id": sample_query.pk_query,
                "endpoint_id": sample_endpoint.pk_endpoint,
                "variables": {"id": "456"}
            }
        ]
        
        results = await execution_service.execute_batch(executions, max_concurrent=2)
        
        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)
```

#### 3. Integration Tests
```python
"""Integration tests for FraiseQL Doctor."""
import pytest
import aiohttp
from aioresponses import aioresponses
from uuid import uuid4

from fraiseql_doctor.services.query import QueryService
from fraiseql_doctor.services.execution import ExecutionService
from fraiseql_doctor.services.health import HealthCheckService
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
from fraiseql_doctor.services.validation import QueryValidator


class TestFraiseQLClientIntegration:
    """Integration tests for FraiseQL client."""
    
    async def test_client_with_real_endpoint(self, sample_endpoint):
        """Test client against mock GraphQL endpoint."""
        with aioresponses() as m:
            # Mock GraphQL response
            m.post(
                str(sample_endpoint.url),
                payload={
                    "data": {
                        "user": {
                            "id": "123",
                            "name": "John Doe",
                            "email": "john@example.com"
                        }
                    },
                    "extensions": {
                        "complexity": {"score": 5}
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            client = FraiseQLClient(sample_endpoint)
            
            query = """
                query GetUser($id: ID!) {
                    user(id: $id) {
                        id
                        name
                        email
                    }
                }
            """
            
            response = await client.execute_query(
                query,
                variables={"id": "123"}
            )
            
            assert response.data is not None
            assert response.data["user"]["id"] == "123"
            assert response.data["user"]["name"] == "John Doe"
            assert response.response_time_ms > 0
            assert response.complexity_score == 5
    
    async def test_client_authentication(self, sample_endpoint):
        """Test client with various authentication methods."""
        with aioresponses() as m:
            # Mock authenticated response
            m.post(
                str(sample_endpoint.url),
                payload={"data": {"authenticated": True}},
                headers={"Content-Type": "application/json"}
            )
            
            client = FraiseQLClient(sample_endpoint)
            
            response = await client.execute_query("query { authenticated }")
            
            assert response.data["authenticated"] is True
            
            # Verify auth header was sent
            assert len(m.requests) == 1
            request = m.requests[0][1]
            assert "Authorization" in request.headers
            assert request.headers["Authorization"] == "Bearer test-token"
    
    async def test_client_error_handling(self, sample_endpoint):
        """Test client error handling scenarios."""
        with aioresponses() as m:
            # Mock error response
            m.post(
                str(sample_endpoint.url),
                status=500,
                payload={"error": "Internal server error"}
            )
            
            client = FraiseQLClient(sample_endpoint)
            
            with pytest.raises(Exception):  # Should raise appropriate exception
                await client.execute_query("query { test }")


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    async def test_complete_query_lifecycle(
        self,
        db_session,
        mock_graphql_server
    ):
        """Test complete query lifecycle from creation to execution."""
        # Initialize services
        validator = QueryValidator()
        query_service = QueryService(db_session, validator)
        
        # Create endpoint
        endpoint = Endpoint(
            pk_endpoint=uuid4(),
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type="none"
        )
        db_session.add(endpoint)
        await db_session.commit()
        
        # Create query
        from fraiseql_doctor.schemas.query import QueryCreate
        query_data = QueryCreate(
            name="user-profile",
            description="Get user profile data",
            query_text="""
                query GetUser($id: ID!) {
                    user(id: $id) {
                        id
                        name
                        email
                    }
                }
            """,
            variables={"id": "123"},
            tags=["user", "profile"],
            created_by="integration-test"
        )
        
        query = await query_service.create_query(query_data)
        assert query.name == "user-profile"
        
        # Execute query
        def client_factory(endpoint):
            return FraiseQLClient(endpoint)
        
        from fraiseql_doctor.services.metrics import MetricsCollector
        metrics = MetricsCollector()
        execution_service = ExecutionService(db_session, client_factory, metrics)
        
        result = await execution_service.execute_query(
            query_id=query.pk_query,
            endpoint_id=endpoint.pk_endpoint
        )
        
        assert result["status"] == "success"
        assert result["data"]["user"]["id"] == "123"
        
        # Verify execution was recorded
        from sqlalchemy import select
        stmt = select(Execution).where(Execution.fk_query == query.pk_query)
        execution_result = await db_session.execute(stmt)
        execution = execution_result.scalar_one()
        
        assert execution.status == "success"
        assert execution.response_time_ms > 0
    
    async def test_health_monitoring_workflow(self, db_session):
        """Test health monitoring workflow."""
        # Create endpoint
        endpoint = Endpoint(
            pk_endpoint=uuid4(),
            name="monitoring-test",
            url="https://api.example.com/graphql",
            auth_type="none",
            health_check_interval_minutes=5
        )
        db_session.add(endpoint)
        await db_session.commit()
        
        # Mock health check
        with aioresponses() as m:
            m.post(
                str(endpoint.url),
                payload={
                    "data": {
                        "__schema": {
                            "queryType": {"name": "Query"},
                            "mutationType": {"name": "Mutation"},
                            "subscriptionType": None
                        }
                    }
                }
            )
            
            def client_factory(endpoint):
                return FraiseQLClient(endpoint)
            
            health_service = HealthCheckService(db_session, client_factory)
            
            result = await health_service.check_endpoint_health(endpoint.pk_endpoint)
            
            assert result["is_healthy"] is True
            assert result["available_operations"] == ["query", "mutation"]
            assert result["response_time_ms"] > 0
            
            # Verify health check was recorded
            from sqlalchemy import select
            from fraiseql_doctor.models.health_check import HealthCheck
            stmt = select(HealthCheck).where(HealthCheck.fk_endpoint == endpoint.pk_endpoint)
            health_result = await db_session.execute(stmt)
            health_check = health_result.scalar_one()
            
            assert health_check.is_healthy is True
            assert health_check.response_time_ms > 0
```

#### 4. Performance Tests
```python
"""Performance and load tests."""
import pytest
import asyncio
import time
from statistics import mean, median

from fraiseql_doctor.services.execution import ExecutionService
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient


class TestPerformance:
    """Performance test suite."""
    
    @pytest.mark.performance
    async def test_concurrent_query_execution(
        self,
        db_session,
        sample_query,
        sample_endpoint,
        mock_graphql_server
    ):
        """Test performance of concurrent query execution."""
        def client_factory(endpoint):
            return FraiseQLClient(endpoint)
        
        from fraiseql_doctor.services.metrics import MetricsCollector
        metrics = MetricsCollector()
        execution_service = ExecutionService(db_session, client_factory, metrics)
        
        # Execute multiple queries concurrently
        num_concurrent = 10
        start_time = time.time()
        
        tasks = [
            execution_service.execute_query(
                query_id=sample_query.pk_query,
                endpoint_id=sample_endpoint.pk_endpoint
            )
            for _ in range(num_concurrent)
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Analyze results
        total_time = end_time - start_time
        successful_results = [r for r in results if r["status"] == "success"]
        response_times = [r["response_time_ms"] for r in successful_results]
        
        assert len(successful_results) == num_concurrent
        assert total_time < 5.0  # Should complete within 5 seconds
        assert mean(response_times) < 1000  # Average response time < 1s
        assert max(response_times) < 2000  # Max response time < 2s
    
    @pytest.mark.performance
    async def test_database_performance(self, db_session):
        """Test database operation performance."""
        from fraiseql_doctor.models.query import Query
        
        # Insert many queries
        num_queries = 100
        start_time = time.time()
        
        queries = []
        for i in range(num_queries):
            query = Query(
                pk_query=uuid4(),
                name=f"perf-test-{i}",
                query_text=f"query Test{i} {{ user(id: \"{i}\") {{ id name }} }}",
                created_by="perf-test"
            )
            queries.append(query)
        
        db_session.add_all(queries)
        await db_session.commit()
        insert_time = time.time() - start_time
        
        # Query performance
        start_time = time.time()
        from sqlalchemy import select
        stmt = select(Query).where(Query.created_by == "perf-test")
        result = await db_session.execute(stmt)
        fetched_queries = result.scalars().all()
        query_time = time.time() - start_time
        
        assert len(fetched_queries) == num_queries
        assert insert_time < 2.0  # Should insert 100 queries in < 2s
        assert query_time < 0.5   # Should query 100 queries in < 0.5s
    
    @pytest.mark.performance
    async def test_memory_usage(self, db_session, sample_query, sample_endpoint):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operations
        def client_factory(endpoint):
            return FraiseQLClient(endpoint)
        
        from fraiseql_doctor.services.metrics import MetricsCollector
        metrics = MetricsCollector()
        execution_service = ExecutionService(db_session, client_factory, metrics)
        
        # Execute many queries to test memory usage
        for _ in range(50):
            try:
                await execution_service.execute_query(
                    query_id=sample_query.pk_query,
                    endpoint_id=sample_endpoint.pk_endpoint
                )
            except:
                pass  # Ignore errors, we're testing memory usage
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory increase should be reasonable (< 100MB for 50 queries)
        assert memory_increase < 100
```

#### 5. Property-Based Tests
```python
"""Property-based testing with Hypothesis."""
import pytest
from hypothesis import given, strategies as st, assume
from hypothesis.strategies import composite
import re

from fraiseql_doctor.services.validation import QueryValidator, ComplexityAnalyzer


@composite
def graphql_query_strategy(draw):
    """Generate valid GraphQL queries."""
    query_type = draw(st.sampled_from(["query", "mutation", "subscription"]))
    operation_name = draw(st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll"]), min_size=1, max_size=20))
    
    # Simple field selection
    fields = draw(st.lists(
        st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll"]), min_size=1, max_size=10),
        min_size=1,
        max_size=5
    ))
    
    field_selection = " ".join(fields)
    
    if query_type == "query":
        return f"query {operation_name} {{ {field_selection} }}"
    elif query_type == "mutation":
        return f"mutation {operation_name} {{ {field_selection} }}"
    else:
        return f"subscription {operation_name} {{ {field_selection} }}"


class TestPropertyBased:
    """Property-based tests."""
    
    @given(graphql_query_strategy())
    def test_query_validation_properties(self, query_text):
        """Test query validation properties."""
        validator = QueryValidator()
        
        # Property: Valid GraphQL syntax should not raise exceptions
        try:
            result = validator.validate_syntax(query_text)
            # If validation succeeds, result should have expected structure
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'errors')
        except Exception as e:
            # If validation fails, it should be for a legitimate reason
            assert isinstance(e, (ValueError, SyntaxError))
    
    @given(st.integers(min_value=1, max_value=100))
    def test_complexity_analyzer_properties(self, field_count):
        """Test complexity analyzer properties."""
        # Generate query with specific field count
        fields = ["field" + str(i) for i in range(field_count)]
        query = "query { " + " ".join(fields) + " }"
        
        analyzer = ComplexityAnalyzer()
        metrics = analyzer.analyze_query(query)
        
        # Property: Field count should correlate with complexity
        assert metrics.field_count >= field_count - 5  # Allow some variance for parsing
        assert metrics.total_score > 0
        assert metrics.depth >= 1
    
    @given(
        st.text(min_size=1, max_size=50),
        st.dictionaries(st.text(), st.text(), min_size=0, max_size=10)
    )
    def test_query_creation_properties(self, name, variables):
        """Test query creation with various inputs."""
        assume(re.match(r'^[a-zA-Z0-9_-]+$', name))  # Valid name format
        
        from fraiseql_doctor.schemas.query import QueryCreate
        
        try:
            query_data = QueryCreate(
                name=name,
                query_text="query { test }",
                variables=variables,
                created_by="property-test"
            )
            
            # Property: Valid inputs should create valid query data
            assert query_data.name == name
            assert query_data.variables == variables
            assert query_data.query_text == "query { test }"
            
        except ValueError:
            # If creation fails, name should be invalid
            assert not re.match(r'^[a-zA-Z0-9_-]+$', name)
```

#### 6. CLI Testing
```python
"""CLI testing with typer test client."""
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, AsyncMock
import json

from fraiseql_doctor.cli.main import app


class TestCLI:
    """CLI testing suite."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "FraiseQL Doctor v0.1.0" in result.stdout
    
    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "FraiseQL Doctor" in result.stdout
        assert "query" in result.stdout
        assert "endpoint" in result.stdout
        assert "health" in result.stdout
    
    @patch('fraiseql_doctor.cli.commands.query_commands.get_query_service')
    def test_query_list_command(self, mock_service):
        """Test query list command."""
        # Mock service response
        mock_query_service = AsyncMock()
        mock_query_service.list_queries.return_value = [
            {
                "pk_query": "123e4567-e89b-12d3-a456-426614174000",
                "name": "test-query",
                "description": "Test query",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
                "tags": ["test"]
            }
        ]
        mock_service.return_value.__aenter__.return_value = mock_query_service
        
        result = self.runner.invoke(app, ["query", "list"])
        
        assert result.exit_code == 0
        assert "test-query" in result.stdout
    
    @patch('fraiseql_doctor.cli.commands.query_commands.get_query_service')
    def test_query_create_command_with_file(self, mock_service, tmp_path):
        """Test query create command with file input."""
        # Create temporary GraphQL file
        query_file = tmp_path / "test.graphql"
        query_file.write_text("query { user { id name } }")
        
        mock_query_service = AsyncMock()
        mock_query_service.create_query.return_value = {
            "pk_query": "123e4567-e89b-12d3-a456-426614174000",
            "name": "test-query"
        }
        mock_service.return_value.__aenter__.return_value = mock_query_service
        
        result = self.runner.invoke(app, [
            "query", "create", "test-query",
            "--file", str(query_file),
            "--description", "Test description"
        ])
        
        assert result.exit_code == 0
        assert "created successfully" in result.stdout
    
    def test_config_init_command(self, tmp_path):
        """Test config initialization command."""
        config_dir = tmp_path / "test-config"
        
        result = self.runner.invoke(app, [
            "config", "init",
            "--dir", str(config_dir)
        ])
        
        assert result.exit_code == 0
        assert "Configuration initialized" in result.stdout
        
        # Verify config file was created
        config_file = config_dir / "config.yaml"
        assert config_file.exists()
        
        # Verify config content
        config_content = config_file.read_text()
        assert "database:" in config_content
        assert "logging:" in config_content
```

### Test Automation and CI/CD

#### 7. GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_USER: test
          POSTGRES_DB: fraiseql_doctor_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        uv sync --dev
    
    - name: Run linting
      run: |
        uv run ruff check .
        uv run ruff format --check .
        uv run mypy src
    
    - name: Run tests
      run: |
        uv run pytest tests/ -v --cov=src --cov-report=xml
      env:
        TEST_DATABASE_URL: postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Run performance tests
      run: |
        uv run pytest tests/ -m performance -v
```

### Success Criteria
- [x] Comprehensive unit tests for all services (>95% coverage)
- [x] Integration tests with mock GraphQL servers
- [x] End-to-end workflow testing
- [x] Performance and load testing
- [x] Property-based testing for edge cases
- [x] CLI testing with various scenarios
- [x] Automated CI/CD pipeline
- [x] Memory usage and resource testing
- [x] Error handling validation
- [x] Database performance testing

### Handoff Notes for Next Phase
- All tests should pass before documentation phase
- Performance benchmarks established for monitoring
- Test database setup should be automated
- CI/CD pipeline should block merges on test failures
- Add mutation testing with mutmut for robustness
- Consider adding contract testing for GraphQL schemas
- Implement test data factories for complex scenarios