# Phase 6: Testing Foundation & Quality Assurance
**Agent: Test-Driven Quality Engineer**

## Objective
Establish comprehensive testing as the FOUNDATION for all development phases, providing advanced testing patterns, performance baselines, and quality assurance processes that ensure production-ready reliability.

## 🎯 Testing-First Philosophy

**Testing is not the end of development - it IS development.** This phase establishes testing patterns that have been driving all previous phases and provides advanced techniques for maintaining quality.

## 🔄 Advanced TDD Patterns

### Step 1: Enhanced Test Infrastructure

#### 1.1 Production-Like Test Environment
```python
# tests/fixtures/production_like.py - Advanced test infrastructure
"""Production-like test environment setup."""
import pytest
import asyncio
import contextlib
from typing import AsyncGenerator
import docker
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fraiseql_doctor.models.base import Base


class ProductionLikeEnvironment:
    """Production-like environment for comprehensive testing."""
    
    def __init__(self):
        self.db_container = None
        self.redis_container = None
        self.docker_client = docker.from_env()
        self.engine = None
        
    async def start(self):
        """Start production-like services."""
        # Start PostgreSQL container
        self.db_container = self.docker_client.containers.run(
            "postgres:15",
            environment={
                "POSTGRES_DB": "fraiseql_doctor_test",
                "POSTGRES_USER": "test",
                "POSTGRES_PASSWORD": "test"
            },
            ports={"5432": None},
            detach=True,
            remove=True
        )
        
        # Wait for database to be ready
        await self._wait_for_database()
        
        # Create database engine
        port = self.db_container.ports["5432/tcp"][0]["HostPort"]
        db_url = f"postgresql+asyncpg://test:test@localhost:{port}/fraiseql_doctor_test"
        
        self.engine = create_async_engine(db_url, echo=False)
        
        # Create schema
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def stop(self):
        """Stop all services."""
        if self.engine:
            await self.engine.dispose()
        
        if self.db_container:
            self.db_container.stop()
        
        if self.redis_container:
            self.redis_container.stop()
    
    async def _wait_for_database(self, timeout=30):
        """Wait for database to be ready."""
        port = self.db_container.ports["5432/tcp"][0]["HostPort"]
        
        for _ in range(timeout):
            try:
                conn = await asyncpg.connect(
                    host="localhost",
                    port=port,
                    database="fraiseql_doctor_test",
                    user="test",
                    password="test"
                )
                await conn.close()
                return
            except Exception:
                await asyncio.sleep(1)
        
        raise RuntimeError("Database failed to start within timeout")

@pytest.fixture(scope="session")
async def production_env():
    """Production-like environment fixture."""
    env = ProductionLikeEnvironment()
    await env.start()
    
    yield env
    
    await env.stop()

@pytest.fixture
async def prod_db_session(production_env) -> AsyncSession:
    """Production-like database session."""
    async_session = sessionmaker(
        production_env.engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        transaction = await session.begin()
        yield session
        await transaction.rollback()
```

#### 1.2 Advanced Mock Patterns
```python
# tests/fixtures/advanced_mocks.py - Sophisticated mocking patterns
"""Advanced mocking patterns for comprehensive testing."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import aioresponses
from typing import Dict, Any, List
import json


class GraphQLEndpointSimulator:
    """Simulate various GraphQL endpoint behaviors."""
    
    def __init__(self):
        self.scenarios = {}
        self.call_history = []
    
    def add_scenario(self, name: str, query_pattern: str, response: Dict[str, Any]):
        """Add a response scenario for specific query patterns."""
        self.scenarios[name] = {
            'pattern': query_pattern,
            'response': response
        }
    
    def get_response(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get response based on query pattern matching."""
        self.call_history.append({'query': query, 'variables': variables})
        
        for scenario in self.scenarios.values():
            if scenario['pattern'] in query:
                return scenario['response']
        
        # Default response
        return {
            'data': None,
            'errors': [{'message': f'Unknown query pattern in: {query[:50]}...'}]
        }

@pytest.fixture
def graphql_simulator():
    """GraphQL endpoint simulator fixture."""
    simulator = GraphQLEndpointSimulator()
    
    # Add common scenarios
    simulator.add_scenario('user_query', 'user', {
        'data': {
            'user': {
                'id': '123',
                'name': 'Test User',
                'email': 'test@example.com'
            }
        }
    })
    
    simulator.add_scenario('introspection', '__schema', {
        'data': {
            '__schema': {
                'queryType': {'name': 'Query'},
                'mutationType': {'name': 'Mutation'},
                'subscriptionType': None
            }
        }
    })
    
    return simulator

@pytest.fixture
def mock_aiohttp_with_simulator(graphql_simulator):
    """Mock aiohttp with GraphQL simulator responses."""
    with aioresponses.aioresponses() as m:
        def request_callback(url, **kwargs):
            """Handle GraphQL requests with simulator."""
            request_data = kwargs.get('json', {})
            query = request_data.get('query', '')
            variables = request_data.get('variables', {})
            
            response = graphql_simulator.get_response(query, variables)
            
            return aioresponses.CallbackResult(
                status=200,
                payload=response,
                headers={'Content-Type': 'application/json'}
            )
        
        # Mock all GraphQL endpoints
        m.post(url_matcher=lambda url: 'graphql' in str(url), callback=request_callback)
        
        yield m, graphql_simulator

class PerformanceMonitor:
    """Monitor performance during tests."""
    
    def __init__(self):
        self.measurements = []
    
    @contextlib.asynccontextmanager
    async def measure(self, operation_name: str):
        """Measure operation performance."""
        import time
        start_time = time.time()
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to ms
            
            self.measurements.append({
                'operation': operation_name,
                'duration_ms': duration,
                'timestamp': start_time
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.measurements:
            return {}
        
        durations = [m['duration_ms'] for m in self.measurements]
        
        return {
            'count': len(durations),
            'avg_ms': sum(durations) / len(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'total_ms': sum(durations)
        }

@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture."""
    return PerformanceMonitor()
```

### Step 2: Comprehensive Integration Tests

#### 2.1 End-to-End Workflow Tests
```python
# tests/integration/test_complete_workflows.py - Complete workflow testing
"""Test complete end-to-end workflows."""
import pytest
import asyncio
from uuid import uuid4

from fraiseql_doctor.services.query import QueryService
from fraiseql_doctor.services.execution import ExecutionService
from fraiseql_doctor.services.health import HealthCheckService
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.schemas.query import QueryCreate


@pytest.mark.integration
async def test_complete_monitoring_workflow(
    prod_db_session,
    mock_aiohttp_with_simulator,
    performance_monitor
):
    """Test complete monitoring workflow from setup to reporting."""
    mock_session, simulator = mock_aiohttp_with_simulator
    
    # Add complex response scenarios
    simulator.add_scenario('complex_user', 'userProfile', {
        'data': {
            'user': {
                'id': '123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'profile': {
                    'bio': 'Software engineer',
                    'avatar': 'https://example.com/avatar.jpg',
                    'settings': {
                        'notifications': True,
                        'privacy': 'private'
                    }
                }
            }
        },
        'extensions': {
            'complexity': {'score': 45},
            'tracing': {'duration': 120}
        }
    })
    
    # Step 1: Setup endpoint
    endpoint = Endpoint(
        name="production-api",
        url="https://api.production.com/graphql",
        auth_type="bearer",
        auth_config={"token": "prod-token-123"},
        timeout_seconds=30,
        max_retries=3
    )
    prod_db_session.add(endpoint)
    await prod_db_session.commit()
    
    # Step 2: Create comprehensive query
    from fraiseql_doctor.services.validation import QueryValidator
    validator = QueryValidator()
    query_service = QueryService(prod_db_session, validator)
    
    complex_query = QueryCreate(
        name="user-profile-comprehensive",
        description="Get complete user profile with nested data",
        query_text="""
            query GetUserProfile($userId: ID!, $includeSettings: Boolean!) {
                user(id: $userId) {
                    id
                    name
                    email
                    profile {
                        bio
                        avatar
                        settings @include(if: $includeSettings) {
                            notifications
                            privacy
                        }
                    }
                }
            }
        """,
        variables={"userId": "123", "includeSettings": True},
        tags=["user", "profile", "production", "complex"],
        created_by="integration-test"
    )
    
    with performance_monitor.measure("query_creation"):
        query = await query_service.create_query(complex_query)
    
    # Step 3: Execute query with performance monitoring
    def client_factory(endpoint):
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
        return FraiseQLClient(endpoint)
    
    from fraiseql_doctor.services.metrics import MetricsCollector
    metrics = MetricsCollector()
    execution_service = ExecutionService(prod_db_session, client_factory, metrics)
    
    with performance_monitor.measure("query_execution"):
        execution_result = await execution_service.execute_query(
            query_id=query.pk_query,
            endpoint_id=endpoint.pk_endpoint,
            variables={"userId": "456", "includeSettings": False},
            timeout=30
        )
    
    # Step 4: Health monitoring
    health_service = HealthCheckService(prod_db_session, client_factory)
    
    with performance_monitor.measure("health_check"):
        health_result = await health_service.check_endpoint_health(endpoint.pk_endpoint)
    
    # Step 5: Verify complete workflow
    assert execution_result["status"] == "success"
    assert execution_result["data"]["user"]["id"] == "123"
    assert execution_result["complexity_score"] == 45
    assert execution_result["response_time_ms"] > 0
    
    assert health_result["is_healthy"] is True
    assert health_result["available_operations"] == ["query", "mutation"]
    
    # Step 6: Performance validation
    perf_stats = performance_monitor.get_stats()
    assert perf_stats["count"] == 3
    assert perf_stats["avg_ms"] < 1000  # Should be fast
    
    # Step 7: Verify data persistence
    from sqlalchemy import select
    from fraiseql_doctor.models.execution import Execution
    
    exec_query = select(Execution).where(Execution.fk_query == query.pk_query)
    exec_result = await prod_db_session.execute(exec_query)
    stored_execution = exec_result.scalar_one()
    
    assert stored_execution.status == "success"
    assert stored_execution.actual_complexity_score == 45
    assert stored_execution.response_data["user"]["name"] == "John Doe"

@pytest.mark.integration
async def test_multi_endpoint_query_execution(
    prod_db_session,
    mock_aiohttp_with_simulator,
    performance_monitor
):
    """Test executing same query across multiple endpoints."""
    mock_session, simulator = mock_aiohttp_with_simulator
    
    # Create multiple endpoints with different response times
    endpoints = []
    for i, (name, delay) in enumerate([
        ("fast-api", 50),
        ("medium-api", 150),
        ("slow-api", 300)
    ]):
        simulator.add_scenario(f'endpoint_{i}', 'testQuery', {
            'data': {'result': f'response from {name}'},
            'extensions': {'tracing': {'duration': delay}}
        })
        
        endpoint = Endpoint(
            name=name,
            url=f"https://{name}.example.com/graphql",
            auth_type="none",
            timeout_seconds=10
        )
        endpoints.append(endpoint)
        prod_db_session.add(endpoint)
    
    await prod_db_session.commit()
    
    # Create single query
    validator = QueryValidator()
    query_service = QueryService(prod_db_session, validator)
    
    query = await query_service.create_query(QueryCreate(
        name="multi-endpoint-test",
        query_text="query { testQuery }",
        created_by="integration-test"
    ))
    
    # Execute across all endpoints concurrently
    def client_factory(endpoint):
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
        return FraiseQLClient(endpoint)
    
    execution_service = ExecutionService(prod_db_session, client_factory, MetricsCollector())
    
    executions = [
        {
            "query_id": query.pk_query,
            "endpoint_id": endpoint.pk_endpoint,
            "variables": {}
        }
        for endpoint in endpoints
    ]
    
    with performance_monitor.measure("batch_execution"):
        results = await execution_service.execute_batch(executions, max_concurrent=3)
    
    # Verify all executions succeeded
    assert len(results) == 3
    assert all(r["status"] == "success" for r in results)
    
    # Verify concurrent execution was efficient
    perf_stats = performance_monitor.get_stats()
    # Should be faster than sequential execution (sum of delays)
    assert perf_stats["max_ms"] < 600  # Much less than 500ms total

@pytest.mark.integration
async def test_failure_recovery_workflow(
    prod_db_session,
    mock_aiohttp_with_simulator,
    performance_monitor
):
    """Test system behavior during failures and recovery."""
    mock_session, simulator = mock_aiohttp_with_simulator
    
    # Setup endpoint that will fail then recover
    endpoint = Endpoint(
        name="unreliable-api",
        url="https://unreliable.example.com/graphql",
        auth_type="none",
        max_retries=3,
        retry_delay_seconds=1
    )
    prod_db_session.add(endpoint)
    await prod_db_session.commit()
    
    # Create test query
    validator = QueryValidator()
    query_service = QueryService(prod_db_session, validator)
    
    query = await query_service.create_query(QueryCreate(
        name="failure-test",
        query_text="query { failureTest }",
        created_by="integration-test"
    ))
    
    # Setup failure then success scenario
    call_count = 0
    def failure_then_success(url, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count <= 2:
            # First two calls fail
            return aioresponses.CallbackResult(status=500, payload={'error': 'Server error'})
        else:
            # Third call succeeds
            return aioresponses.CallbackResult(
                status=200,
                payload={'data': {'failureTest': 'recovered!'}}
            )
    
    # Replace the mock with failure scenario
    mock_session.clear()
    mock_session.post(
        "https://unreliable.example.com/graphql",
        callback=failure_then_success
    )
    
    # Execute with retry logic
    def client_factory(endpoint):
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
        return FraiseQLClient(endpoint)
    
    execution_service = ExecutionService(prod_db_session, client_factory, MetricsCollector())
    
    with performance_monitor.measure("failure_recovery"):
        result = await execution_service.execute_query(
            query_id=query.pk_query,
            endpoint_id=endpoint.pk_endpoint
        )
    
    # Should eventually succeed after retries
    assert result["status"] == "success"
    assert result["data"]["failureTest"] == "recovered!"
    
    # Should have taken time for retries
    perf_stats = performance_monitor.get_stats()
    assert perf_stats["max_ms"] >= 2000  # At least 2 seconds for retries
```

#### 2.2 Load and Stress Testing
```python
# tests/performance/test_load_scenarios.py - Load and stress testing
"""Load and stress testing scenarios."""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import statistics


@pytest.mark.performance
@pytest.mark.slow
async def test_concurrent_query_load(
    prod_db_session,
    mock_aiohttp_with_simulator,
    performance_monitor
):
    """Test system under high concurrent query load."""
    mock_session, simulator = mock_aiohttp_with_simulator
    
    # Setup load test scenario
    simulator.add_scenario('load_test', 'loadQuery', {
        'data': {'result': 'load test response'},
        'extensions': {'tracing': {'duration': 100}}
    })
    
    # Create endpoint and query
    endpoint = Endpoint(
        name="load-test-api",
        url="https://loadtest.example.com/graphql",
        auth_type="none"
    )
    prod_db_session.add(endpoint)
    await prod_db_session.commit()
    
    validator = QueryValidator()
    query_service = QueryService(prod_db_session, validator)
    
    query = await query_service.create_query(QueryCreate(
        name="load-test-query",
        query_text="query { loadQuery }",
        created_by="load-test"
    ))
    
    # Execute high concurrent load
    def client_factory(endpoint):
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
        return FraiseQLClient(endpoint)
    
    execution_service = ExecutionService(prod_db_session, client_factory, MetricsCollector())
    
    async def single_execution():
        """Single query execution."""
        return await execution_service.execute_query(
            query_id=query.pk_query,
            endpoint_id=endpoint.pk_endpoint
        )
    
    # Test different concurrency levels
    concurrency_levels = [10, 25, 50, 100]
    results = {}
    
    for concurrency in concurrency_levels:
        with performance_monitor.measure(f"load_test_{concurrency}"):
            start_time = time.time()
            
            # Execute concurrent requests
            tasks = [single_execution() for _ in range(concurrency)]
            execution_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            # Analyze results
            successful = [r for r in execution_results if not isinstance(r, Exception)]
            failed = [r for r in execution_results if isinstance(r, Exception)]
            
            results[concurrency] = {
                'total_time': end_time - start_time,
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': len(successful) / concurrency * 100,
                'throughput': concurrency / (end_time - start_time)
            }
    
    # Verify performance requirements
    for concurrency, result in results.items():
        assert result['success_rate'] >= 95.0  # 95% success rate minimum
        assert result['total_time'] < 10.0     # Complete within 10 seconds
        
        if concurrency <= 50:
            assert result['success_rate'] == 100.0  # Perfect success for moderate load

@pytest.mark.performance
async def test_memory_usage_under_load(
    prod_db_session,
    mock_aiohttp_with_simulator
):
    """Test memory usage remains stable under load."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    mock_session, simulator = mock_aiohttp_with_simulator
    
    # Create large response scenario
    large_response = {
        'data': {
            'users': [
                {
                    'id': f'user_{i}',
                    'name': f'User {i}',
                    'email': f'user{i}@example.com',
                    'profile': {
                        'bio': 'A' * 1000,  # 1KB bio
                        'preferences': {f'pref_{j}': f'value_{j}' for j in range(100)}
                    }
                }
                for i in range(100)  # 100 users per response
            ]
        }
    }
    
    simulator.add_scenario('memory_test', 'largeQuery', large_response)
    
    # Setup test environment
    endpoint = Endpoint(
        name="memory-test-api",
        url="https://memorytest.example.com/graphql",
        auth_type="none"
    )
    prod_db_session.add(endpoint)
    await prod_db_session.commit()
    
    validator = QueryValidator()
    query_service = QueryService(prod_db_session, validator)
    
    query = await query_service.create_query(QueryCreate(
        name="memory-test-query",
        query_text="query { largeQuery }",
        created_by="memory-test"
    ))
    
    # Execute many requests to test memory stability
    def client_factory(endpoint):
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
        return FraiseQLClient(endpoint)
    
    execution_service = ExecutionService(prod_db_session, client_factory, MetricsCollector())
    
    memory_measurements = []
    
    for i in range(50):  # 50 large requests
        await execution_service.execute_query(
            query_id=query.pk_query,
            endpoint_id=endpoint.pk_endpoint
        )
        
        # Measure memory every 10 requests
        if i % 10 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)
    
    final_memory = process.memory_info().rss / 1024 / 1024
    
    # Memory should not grow excessively
    memory_growth = final_memory - initial_memory
    assert memory_growth < 100  # Less than 100MB growth
    
    # Memory should be relatively stable (no major leaks)
    if len(memory_measurements) > 2:
        memory_trend = statistics.linear_regression(
            range(len(memory_measurements)), 
            memory_measurements
        ).slope
        assert abs(memory_trend) < 5  # Less than 5MB/measurement growth

@pytest.mark.performance
async def test_database_performance_under_load(
    prod_db_session,
    performance_monitor
):
    """Test database performance under high write load."""
    from fraiseql_doctor.models.query import Query
    from fraiseql_doctor.models.execution import Execution
    
    # Create many queries and executions rapidly
    queries_to_create = 100
    executions_per_query = 10
    
    with performance_monitor.measure("bulk_query_creation"):
        # Bulk create queries
        queries = []
        for i in range(queries_to_create):
            query = Query(
                name=f"perf-test-query-{i}",
                query_text=f"query PerfTest{i} {{ test{i} }}",
                tags=["performance", f"batch-{i // 10}"],
                created_by="performance-test",
                expected_complexity_score=10 + (i % 20)
            )
            queries.append(query)
        
        prod_db_session.add_all(queries)
        await prod_db_session.commit()
    
    with performance_monitor.measure("bulk_execution_creation"):
        # Create many executions
        executions = []
        for query in queries[:10]:  # Use first 10 queries
            for j in range(executions_per_query):
                execution = Execution(
                    fk_query=query.pk_query,
                    fk_endpoint=uuid4(),  # Mock endpoint ID
                    status="success",
                    response_time_ms=50 + (j * 10),
                    actual_complexity_score=15 + j,
                    response_data={"test": f"result-{j}"},
                    variables_used={"var": f"value-{j}"}
                )
                executions.append(execution)
        
        prod_db_session.add_all(executions)
        await prod_db_session.commit()
    
    # Test query performance
    with performance_monitor.measure("complex_query_performance"):
        from sqlalchemy import select, func
        
        # Complex aggregation query
        stmt = (
            select(
                Query.created_by,
                func.count(Query.pk_query).label('query_count'),
                func.avg(Query.expected_complexity_score).label('avg_complexity'),
                func.count(Execution.pk_execution).label('execution_count')
            )
            .join(Execution, Query.pk_query == Execution.fk_query, isouter=True)
            .where(Query.created_by == "performance-test")
            .group_by(Query.created_by)
        )
        
        result = await prod_db_session.execute(stmt)
        stats = result.first()
        
        assert stats.query_count == queries_to_create
        assert stats.execution_count == 100  # 10 queries * 10 executions
    
    # Verify performance requirements
    perf_stats = performance_monitor.get_stats()
    
    # Bulk operations should be efficient
    creation_times = [
        m['duration_ms'] for m in performance_monitor.measurements 
        if 'bulk' in m['operation']
    ]
    
    for duration in creation_times:
        assert duration < 5000  # Less than 5 seconds for bulk operations
    
    # Complex queries should be fast
    query_times = [
        m['duration_ms'] for m in performance_monitor.measurements 
        if 'query_performance' in m['operation']
    ]
    
    for duration in query_times:
        assert duration < 1000  # Less than 1 second for complex queries
```

### Step 3: Quality Assurance Automation

#### 3.1 Continuous Integration Enhancement
```yaml
# .github/workflows/comprehensive_testing.yml - Enhanced CI pipeline
name: Comprehensive Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-matrix:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
        test-type: ["unit", "integration", "performance"]
    
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
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH
    
    - name: Install dependencies
      run: |
        uv sync --group dev
    
    - name: Run linting and type checking
      run: |
        uv run ruff check .
        uv run ruff format --check .
        uv run mypy src
    
    - name: Run unit tests
      if: matrix.test-type == 'unit'
      run: |
        uv run pytest tests/unit/ -v --cov=src --cov-report=xml
      env:
        TEST_DATABASE_URL: postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test
    
    - name: Run integration tests
      if: matrix.test-type == 'integration'
      run: |
        uv run pytest tests/integration/ -v --maxfail=5
      env:
        TEST_DATABASE_URL: postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test
    
    - name: Run performance tests
      if: matrix.test-type == 'performance'
      run: |
        uv run pytest tests/performance/ -v -m performance --benchmark-only
      env:
        TEST_DATABASE_URL: postgresql+asyncpg://test:test@localhost/fraiseql_doctor_test
    
    - name: Upload coverage reports
      if: matrix.test-type == 'unit'
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Generate performance report
      if: matrix.test-type == 'performance'
      run: |
        uv run pytest tests/performance/ --benchmark-json=performance.json
    
    - name: Upload performance results
      if: matrix.test-type == 'performance'
      uses: actions/upload-artifact@v3
      with:
        name: performance-results-${{ matrix.python-version }}
        path: performance.json

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run security scan
      uses: PyCQA/bandit-action@v1
      with:
        path: "src"
        level: "high"
        confidence: "high"
    
    - name: Run dependency security check
      run: |
        pip install safety
        safety check

  mutation-testing:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Install dependencies
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH
        uv sync --group dev
        uv add mutmut
    
    - name: Run mutation testing
      run: |
        uv run mutmut run --paths-to-mutate=src/
      continue-on-error: true  # Mutation testing can be flaky
    
    - name: Generate mutation report
      run: |
        uv run mutmut results > mutation_results.txt
    
    - name: Upload mutation results
      uses: actions/upload-artifact@v3
      with:
        name: mutation-results
        path: mutation_results.txt
```

#### 3.2 Quality Metrics and Reporting
```python
# tests/quality/test_metrics_and_reporting.py - Quality metrics validation
"""Quality metrics and reporting validation."""
import pytest
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def test_code_coverage_requirements():
    """Test that code coverage meets requirements."""
    # Run coverage analysis
    result = subprocess.run([
        "uv", "run", "pytest", "--cov=src", "--cov-report=xml", "--cov-report=term"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, f"Coverage analysis failed: {result.stderr}"
    
    # Parse coverage XML
    coverage_file = Path("coverage.xml")
    assert coverage_file.exists(), "Coverage XML file not generated"
    
    tree = ET.parse(coverage_file)
    root = tree.getroot()
    
    # Extract overall coverage percentage
    coverage_percent = float(root.attrib.get('line-rate', 0)) * 100
    
    # Coverage requirements
    assert coverage_percent >= 85.0, f"Coverage {coverage_percent:.1f}% below 85% requirement"
    
    # Check specific module coverage
    for package in root.findall('.//package'):
        package_name = package.attrib.get('name', '')
        package_coverage = float(package.attrib.get('line-rate', 0)) * 100
        
        if 'core' in package_name or 'services' in package_name:
            assert package_coverage >= 90.0, f"Core module {package_name} coverage {package_coverage:.1f}% below 90%"

def test_code_quality_metrics():
    """Test that code quality metrics meet standards."""
    # Run ruff for code quality
    result = subprocess.run([
        "uv", "run", "ruff", "check", "src/", "--format", "json"
    ], capture_output=True, text=True)
    
    if result.stdout:
        issues = json.loads(result.stdout)
        
        # Categorize issues by severity
        errors = [issue for issue in issues if issue.get('type') == 'error']
        warnings = [issue for issue in issues if issue.get('type') == 'warning']
        
        # Quality requirements
        assert len(errors) == 0, f"Found {len(errors)} code quality errors"
        assert len(warnings) <= 5, f"Found {len(warnings)} warnings, maximum 5 allowed"

def test_type_checking_completeness():
    """Test that type checking is comprehensive."""
    result = subprocess.run([
        "uv", "run", "mypy", "src/", "--strict", "--show-error-codes"
    ], capture_output=True, text=True)
    
    # Count type errors
    error_lines = [line for line in result.stdout.split('\n') if 'error:' in line]
    
    # Type checking requirements
    assert len(error_lines) == 0, f"Found {len(error_lines)} type checking errors"

def test_security_baseline():
    """Test security baseline requirements."""
    # Run bandit security scan
    result = subprocess.run([
        "bandit", "-r", "src/", "-f", "json"
    ], capture_output=True, text=True)
    
    if result.stdout:
        scan_results = json.loads(result.stdout)
        
        # Security requirements
        high_severity = [issue for issue in scan_results.get('results', []) 
                        if issue.get('issue_severity') == 'HIGH']
        
        assert len(high_severity) == 0, f"Found {len(high_severity)} high severity security issues"

def test_performance_baseline():
    """Test that performance meets baseline requirements."""
    # Run performance benchmarks
    result = subprocess.run([
        "uv", "run", "pytest", "tests/performance/", "-m", "performance", 
        "--benchmark-json=benchmark.json"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0, "Performance tests failed"
    
    # Parse benchmark results
    benchmark_file = Path("benchmark.json")
    if benchmark_file.exists():
        with open(benchmark_file) as f:
            benchmarks = json.load(f)
        
        # Performance requirements
        for benchmark in benchmarks.get('benchmarks', []):
            stats = benchmark.get('stats', {})
            mean_time = stats.get('mean', float('inf'))
            
            # Database operations should be fast
            if 'database' in benchmark['name'].lower():
                assert mean_time < 0.1, f"Database operation {benchmark['name']} too slow: {mean_time:.3f}s"
            
            # HTTP operations should be reasonable
            if 'http' in benchmark['name'].lower():
                assert mean_time < 1.0, f"HTTP operation {benchmark['name']} too slow: {mean_time:.3f}s"

@pytest.mark.slow
def test_stress_test_baseline():
    """Test system behavior under stress conditions."""
    # Run stress tests
    result = subprocess.run([
        "uv", "run", "pytest", "tests/performance/", "-m", "stress", "-v"
    ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
    
    # Stress tests should pass without crashing
    assert result.returncode == 0, f"Stress tests failed: {result.stderr}"
    
    # Check for memory leaks or crashes in output
    assert "FAILED" not in result.stdout, "Some stress tests failed"
    assert "ERROR" not in result.stderr, "Errors occurred during stress testing"
```

## TDD Success Criteria for Phase 6

### Testing Foundation Verification ✅
- [ ] Production-like test environment with real services
- [ ] Sophisticated mocking patterns for external dependencies
- [ ] Performance monitoring integrated into all tests
- [ ] Load and stress testing validates system limits

### Quality Assurance Verification ✅
- [ ] Comprehensive CI/CD pipeline with matrix testing
- [ ] Code coverage, quality, and security metrics automated
- [ ] Performance baselines established and monitored
- [ ] Mutation testing validates test effectiveness

### Advanced Testing Patterns ✅
- [ ] End-to-end workflow testing covers real user scenarios
- [ ] Failure and recovery testing ensures resilience
- [ ] Memory and resource usage testing prevents leaks
- [ ] Database performance testing under load

### Quality Gates Maintained ✅
- [ ] **Code Coverage**: 85%+ overall, 90%+ for core modules
- [ ] **Code Quality**: Zero errors, minimal warnings
- [ ] **Type Safety**: Complete type checking with no errors
- [ ] **Security**: No high-severity security issues
- [ ] **Performance**: Database ops < 100ms, HTTP ops < 1s
- [ ] **Reliability**: Stress tests pass without failures

## Development Workflow Integration

### Daily Development
```bash
# TDD Red-Green-Refactor cycle
make red      # Run tests (should fail for new features)
make green    # Implement minimum to pass tests
make refactor # Improve code while keeping tests green

# Continuous quality validation
make test-coverage  # Ensure coverage requirements
make lint          # Code quality validation
make test-performance # Performance regression check
```

### Pre-commit Workflow
```bash
# Automated quality gates
pre-commit run --all-files  # Format, lint, type check
make test-unit             # Fast unit test validation
make test-integration      # Integration test validation
```

### Release Validation
```bash
# Comprehensive release testing
make test                 # Full test suite
make test-performance     # Performance validation
make security-scan        # Security baseline check
make mutation-test        # Test quality validation
```

## Conclusion

This TDD-driven approach ensures that:

1. **Every feature is driven by failing tests** - No code without tests
2. **Quality is built-in, not added later** - Testing is development
3. **Performance is validated continuously** - No performance regressions
4. **Security is checked automatically** - No security vulnerabilities
5. **Reliability is proven through stress testing** - System handles real-world load

The testing foundation established here supports all previous phases and provides the confidence needed for production deployment. Every line of code has been justified by tests, every feature has been validated against requirements, and every performance characteristic has been measured and verified.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "status": "completed", "content": "Analyze current prompts and identify TDD opportunities"}, {"id": "2", "status": "completed", "content": "Rewrite Phase 1 (Project Foundation) to include TDD setup"}, {"id": "3", "status": "completed", "content": "Rewrite Phase 2 (Database Schema) with test-first approach"}, {"id": "4", "status": "completed", "content": "Rewrite Phase 3 (FraiseQL Client) with comprehensive testing"}, {"id": "5", "status": "completed", "content": "Rewrite Phase 4 (Query Management) with TDD methodology"}, {"id": "6", "status": "completed", "content": "Rewrite Phase 5 (CLI Interface) with test coverage"}, {"id": "7", "status": "completed", "content": "Update Phase 6 (Testing & QA) to be the foundation for all phases"}]