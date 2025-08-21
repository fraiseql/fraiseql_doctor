"""Real implementation fixtures for integration testing."""

from uuid import uuid4

import pytest

from src.fraiseql_doctor.core.execution_manager import ExecutionConfig, QueryExecutionManager
from src.fraiseql_doctor.core.query_collection import QueryCollectionManager
from src.fraiseql_doctor.core.result_storage import (
    ResultStorageManager,
    StorageBackend,
    StorageConfig,
)
from src.fraiseql_doctor.models.query import Query
from src.fraiseql_doctor.models.query_collection import QueryCollection

from .real_services import (
    TestComplexityAnalyzer,
    create_test_client_factory,
    create_test_endpoint,
)


@pytest.fixture()
def test_complexity_analyzer():
    """Create test complexity analyzer."""
    return TestComplexityAnalyzer()


@pytest.fixture()
def test_client_factory():
    """Create test GraphQL client factory."""
    return create_test_client_factory()


@pytest.fixture()
async def test_endpoint():
    """Create test endpoint."""
    return await create_test_endpoint()


@pytest.fixture()
def real_query_collection_manager(db_session, test_complexity_analyzer):
    """Create real QueryCollectionManager with existing database session."""
    return QueryCollectionManager(db_session, test_complexity_analyzer)


@pytest.fixture()
def real_execution_manager(db_session, test_client_factory, real_query_collection_manager):
    """Create real QueryExecutionManager with existing database session."""
    config = ExecutionConfig(timeout_seconds=30, max_retries=2, max_concurrent=5, batch_size=10)
    return QueryExecutionManager(
        db_session, test_client_factory, real_query_collection_manager, config
    )


@pytest.fixture()
def real_result_storage_manager(db_session, tmp_path):
    """Create real ResultStorageManager with existing database session."""
    storage_path = tmp_path / "test_results"
    config = StorageConfig(
        backend=StorageBackend.FILE_SYSTEM,
        file_base_path=storage_path,
        max_size_mb=10,
        cache_threshold_kb=100,
        ttl_hours=1,
    )
    return ResultStorageManager(db_session, config)


@pytest.fixture()
def sample_query_data():
    """Sample query data for testing."""
    return {
        "name": "Test Query",
        "query_text": "query { users { id name email } }",
        "variables": {"limit": 10},
        "created_by": "test-user",
    }


@pytest.fixture()
def sample_collection_data():
    """Sample collection data for testing."""
    return {
        "name": "Test Collection",
        "description": "Integration test collection",
        "tags": ["test", "integration"],
        "created_by": "test-user",
    }


@pytest.fixture()
def sample_queries():
    """Sample GraphQL queries for testing."""
    return [
        {
            "name": "Get Users",
            "query_text": """
                query GetUsers($limit: Int) {
                    users(limit: $limit) {
                        id
                        name
                        email
                    }
                }
            """,
            "variables": {"limit": 10},
            "created_by": "test-user",
            "priority": "medium",
        },
        {
            "name": "Get User Profile",
            "query_text": """
                query GetUserProfile($userId: ID!) {
                    user(id: $userId) {
                        id
                        name
                        email
                        profile {
                            bio
                            avatar
                        }
                    }
                }
            """,
            "variables": {"userId": "123"},
            "created_by": "test-user",
            "priority": "high",
        },
        {
            "name": "Complex Dashboard Query",
            "query_text": """
                query GetDashboard {
                    dashboard {
                        stats {
                            totalUsers
                            activeUsers
                            revenue
                        }
                        recentActivity {
                            id
                            type
                            user {
                                name
                                avatar
                            }
                            timestamp
                        }
                        charts {
                            userGrowth
                            revenueByMonth
                        }
                    }
                }
            """,
            "variables": {},
            "created_by": "test-user",
            "priority": "low",
        },
    ]


@pytest.fixture()
def created_query(real_query_collection_manager, sample_query_data):
    """Create a real query instance for testing."""
    # Create query using real services
    query = Query.from_dict(
        {**sample_query_data, "pk_query": uuid4(), "status": "active", "priority": "medium"}
    )

    # Configure complexity analyzer with predictable result
    real_query_collection_manager.complexity_analyzer.set_custom_score(5.0)

    return query


@pytest.fixture()
def created_collection(real_query_collection_manager, sample_collection_data):
    """Create a real collection instance for testing."""
    collection = QueryCollection.from_dict(
        {**sample_collection_data, "pk_query_collection": uuid4()}
    )
    return collection


@pytest.fixture()
async def created_collection_with_queries(real_query_collection_manager, sample_queries):
    """Create a real collection with queries for testing."""
    from src.fraiseql_doctor.core.database.schemas import QueryCollectionCreate, QueryCreate

    # Configure analyzer to not fail
    real_query_collection_manager.complexity_analyzer.set_custom_score(5.0)
    real_query_collection_manager.get_collection_by_name = lambda name: None

    collection_schema = QueryCollectionCreate(
        name="Integration Test Collection",
        description="Collection with real queries",
        created_by="test-user",
        initial_queries=[QueryCreate(**query) for query in sample_queries],
    )

    collection = await real_query_collection_manager.create_collection(collection_schema)
    return collection
