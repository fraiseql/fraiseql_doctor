"""Tests for database models."""

import pytest
from datetime import datetime
from uuid import uuid4

from fraiseql_doctor.models import (
    Endpoint,
    AuthType,
    Query,
    QueryType,
    QueryExecution,
    ExecutionStatus,
    HealthCheck,
    HealthStatus,
    ScheduledQuery,
    ScheduleStatus,
)


def test_endpoint_creation() -> None:
    """Test endpoint model creation."""
    endpoint = Endpoint(
        name="test-endpoint",
        description="Test GraphQL endpoint",
        url="https://api.example.com/graphql",
        auth_type=AuthType.BEARER,
        auth_config={"token": "test-token"},
        timeout_seconds=30,
        max_retries=3,
        is_active=True,  # Explicitly set for testing
        total_requests=0,
        total_failures=0
    )
    
    assert endpoint.name == "test-endpoint"
    assert endpoint.url == "https://api.example.com/graphql"
    assert endpoint.auth_type == AuthType.BEARER
    assert endpoint.is_active is True
    assert endpoint.success_rate == 100.0  # No requests yet
    assert endpoint.is_healthy is True


def test_endpoint_stats_update() -> None:
    """Test endpoint statistics updates."""
    endpoint = Endpoint(
        name="test-endpoint",
        url="https://api.example.com/graphql",
        is_active=True,
        total_requests=0,
        total_failures=0
    )
    
    # Simulate successful request
    endpoint.update_stats(success=True, response_time_ms=150.0)
    assert endpoint.total_requests == 1
    assert endpoint.total_failures == 0
    assert endpoint.avg_response_time_ms == 150.0
    assert endpoint.success_rate == 100.0
    
    # Simulate failed request
    endpoint.update_stats(success=False, response_time_ms=300.0)
    assert endpoint.total_requests == 2
    assert endpoint.total_failures == 1
    assert endpoint.success_rate == 50.0


def test_query_creation() -> None:
    """Test query model creation."""
    query = Query(
        name="user-profile",
        description="Get user profile information",
        query_text="query GetUser($id: ID!) { user(id: $id) { id name email } }",
        query_type=QueryType.QUERY,
        default_variables={"id": "123"},
        tags=["user", "profile"],
        total_executions=0,
        total_failures=0,
        is_active=True
    )
    
    assert query.name == "user-profile"
    assert query.query_type == QueryType.QUERY
    assert query.default_variables == {"id": "123"}
    assert query.tags == ["user", "profile"]
    assert query.success_rate == 100.0  # No executions yet


def test_query_validation() -> None:
    """Test query validation methods."""
    query = Query(
        name="test-query",
        query_text="query GetUser($id: ID!) { user(id: $id) { id name } }",
        query_type=QueryType.QUERY
    )
    
    errors = query.validate_query_syntax()
    assert len(errors) == 0  # Should be valid
    
    variables = query.extract_variables()
    assert variables == ["id"]


def test_query_validation_errors() -> None:
    """Test query validation with errors."""
    # Test unbalanced braces
    query = Query(
        name="broken-query",
        query_text="query GetUser { user { id name }",  # Missing closing brace
        query_type=QueryType.QUERY
    )
    
    errors = query.validate_query_syntax()
    assert len(errors) > 0
    assert "Unbalanced braces" in errors[0]


def test_query_execution_creation() -> None:
    """Test query execution model."""
    execution = QueryExecution(
        query_id=uuid4(),
        endpoint_id=uuid4(),
        status=ExecutionStatus.PENDING,
        variables={"id": "123"}
    )
    
    assert execution.status == ExecutionStatus.PENDING
    assert execution.variables == {"id": "123"}
    assert execution.is_successful is False


def test_query_execution_completion() -> None:
    """Test query execution completion."""
    execution = QueryExecution(
        query_id=uuid4(),
        endpoint_id=uuid4(),
        status=ExecutionStatus.RUNNING
    )
    
    execution.mark_completed(ExecutionStatus.SUCCESS, 250.0)
    assert execution.status == ExecutionStatus.SUCCESS
    assert execution.response_time_ms == 250.0
    assert execution.is_successful is True


def test_health_check_creation() -> None:
    """Test health check model."""
    health_check = HealthCheck(
        endpoint_id=uuid4(),
        status=HealthStatus.HEALTHY,
        response_time_ms=100.0,
        check_type="basic"
    )
    
    assert health_check.status == HealthStatus.HEALTHY
    assert health_check.response_time_ms == 100.0
    assert health_check.is_healthy is True


def test_health_check_status_updates() -> None:
    """Test health check status updates."""
    health_check = HealthCheck(
        endpoint_id=uuid4()
    )
    
    # Test healthy status
    health_check.set_healthy(120.0, {"endpoint": "responsive"})
    assert health_check.status == HealthStatus.HEALTHY
    assert health_check.response_time_ms == 120.0
    assert health_check.details == {"endpoint": "responsive"}
    assert health_check.error_message is None
    
    # Test unhealthy status
    health_check.set_unhealthy("Connection timeout", {"timeout": 30})
    assert health_check.status == HealthStatus.UNHEALTHY
    assert health_check.error_message == "Connection timeout"
    assert health_check.details == {"timeout": 30}


def test_scheduled_query_creation() -> None:
    """Test scheduled query model."""
    scheduled_query = ScheduledQuery(
        name="daily-health-check",
        description="Daily health check for API",
        query_id=uuid4(),
        endpoint_id=uuid4(),
        cron_expression="0 9 * * *",  # Daily at 9 AM
        variables={"check": "health"},
        status=ScheduleStatus.ACTIVE,
        is_active=True,
        consecutive_failures=0,
        total_runs=0,
        successful_runs=0,
        failed_runs=0,
        failure_threshold_reached=False,
        max_consecutive_failures=5
    )
    
    assert scheduled_query.name == "daily-health-check"
    assert scheduled_query.cron_expression == "0 9 * * *"
    assert scheduled_query.status == ScheduleStatus.ACTIVE
    assert scheduled_query.is_healthy is True


def test_scheduled_query_cron_validation() -> None:
    """Test cron expression validation."""
    scheduled_query = ScheduledQuery(
        name="test-schedule",
        query_id=uuid4(),
        endpoint_id=uuid4(),
        cron_expression="0 9 * * *"  # Valid cron
    )
    
    assert scheduled_query.validate_cron_expression() is True
    
    # Test invalid cron
    scheduled_query.cron_expression = "invalid cron"
    assert scheduled_query.validate_cron_expression() is False


def test_scheduled_query_execution_recording() -> None:
    """Test recording execution results."""
    scheduled_query = ScheduledQuery(
        name="test-schedule",
        query_id=uuid4(),
        endpoint_id=uuid4(),
        cron_expression="0 9 * * *",
        total_runs=0,
        successful_runs=0,
        failed_runs=0,
        consecutive_failures=0,
        max_consecutive_failures=5
    )
    
    # Record successful execution
    scheduled_query.record_execution(success=True, execution_id=uuid4())
    assert scheduled_query.total_runs == 1
    assert scheduled_query.successful_runs == 1
    assert scheduled_query.consecutive_failures == 0
    assert scheduled_query.success_rate == 100.0
    
    # Record failed execution
    scheduled_query.record_execution(success=False, error_message="Network error")
    assert scheduled_query.total_runs == 2
    assert scheduled_query.failed_runs == 1
    assert scheduled_query.consecutive_failures == 1
    assert scheduled_query.last_error_message == "Network error"
    assert scheduled_query.success_rate == 50.0


def test_scheduled_query_failure_threshold() -> None:
    """Test failure threshold handling."""
    scheduled_query = ScheduledQuery(
        name="test-schedule",
        query_id=uuid4(),
        endpoint_id=uuid4(),
        cron_expression="0 9 * * *",
        max_consecutive_failures=3,
        consecutive_failures=0,
        total_runs=0,
        failed_runs=0,
        status=ScheduleStatus.ACTIVE,
        failure_threshold_reached=False,
        is_active=True
    )
    
    # Record multiple failures
    for i in range(3):
        scheduled_query.record_execution(success=False, error_message=f"Error {i}")
    
    assert scheduled_query.consecutive_failures == 3
    assert scheduled_query.failure_threshold_reached is True
    assert scheduled_query.status == ScheduleStatus.ERROR
    assert scheduled_query.is_healthy is False
    
    # Reset failures
    scheduled_query.reset_failures()
    assert scheduled_query.consecutive_failures == 0
    assert scheduled_query.failure_threshold_reached is False
    assert scheduled_query.status == ScheduleStatus.ACTIVE