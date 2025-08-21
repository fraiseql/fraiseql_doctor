"""Simple executions API for testing connectivity."""

from fastapi import APIRouter, Query as QueryParam
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fraiseql_doctor.web.schemas.execution import ExecutionResponse, ExecutionListResponse

executions_router = APIRouter()


@executions_router.get("/", response_model=ExecutionListResponse)
async def get_query_history(
    endpoint_id: Optional[str] = QueryParam(None, description="Filter by endpoint ID"),
    success: Optional[bool] = QueryParam(None, description="Filter by success status"),
    search: Optional[str] = QueryParam(None, description="Search in query text and operation names"),
    favorite: Optional[bool] = QueryParam(None, description="Filter favorites"),
    from_date: Optional[datetime] = QueryParam(None, description="Filter from date"),
    to_date: Optional[datetime] = QueryParam(None, description="Filter to date"),
    limit: int = QueryParam(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = QueryParam(0, ge=0, description="Offset for pagination")
):
    """
    Get query execution history with filtering and pagination.
    
    This endpoint maps to the frontend Query History feature.
    Returns mock data for testing connectivity.
    """
    
    # Create mock data for testing
    mock_executions = []
    
    # Apply basic filtering to mock data
    total_count = 25  # Simulate total count
    
    if search:
        total_count = 5  # Simulate fewer results when searching
    
    if success is not None:
        total_count = 15 if success else 10
    
    # Generate mock records
    for i in range(min(limit, 10)):  # Return up to 10 mock records
        if offset > 0 and i < offset:
            continue
            
        # Create realistic mock data
        started_time = datetime.now() - timedelta(hours=i, minutes=i*5)
        completed_time = started_time + timedelta(minutes=2, seconds=i*10)
        
        is_success = (i % 4 != 0) if success is None else success
        
        mock_executions.append({
            "id": str(uuid4()),
            "endpoint_id": endpoint_id or str(uuid4()),
            "query_id": str(uuid4()),
            "status": "success" if is_success else "error",
            "operation_name": f"GetUser{i + 1}" if not search else f"Search{search}{i}",
            "started_at": started_time.isoformat(),
            "completed_at": completed_time.isoformat(),
            "response_time_ms": 120 + (i * 15),
            "complexity_score": 3 + (i % 8),
            "error_message": None if is_success else f"Database connection timeout (mock error {i})",
            "variables": {"userId": f"user_{i+100}", "limit": 20},
            "trace_id": f"trace-{i+1000}"
        })
    
    return ExecutionListResponse(
        executions=mock_executions,
        total=total_count,
        limit=limit,
        offset=offset
    )


@executions_router.get("/stats")
async def get_query_stats(
    endpoint_id: Optional[str] = QueryParam(None, description="Filter by endpoint ID"),
    from_date: Optional[datetime] = QueryParam(None, description="Filter from date"),
    to_date: Optional[datetime] = QueryParam(None, description="Filter to date")
):
    """Get query execution statistics."""
    
    # Return mock statistics
    return {
        "total_queries": 1247,
        "successful_queries": 1089,
        "failed_queries": 158,
        "average_response_time": 185.5
    }


@executions_router.post("/")
async def add_query_execution(execution_data: dict):
    """Add a new query execution record."""
    
    # Mock successful creation
    mock_execution = {
        "id": str(uuid4()),
        "endpoint_id": execution_data.get("endpoint_id", str(uuid4())),
        "query_id": str(uuid4()),
        "status": "success",
        "operation_name": execution_data.get("operation_name", "TestQuery"),
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "response_time_ms": execution_data.get("execution_time", 150),
        "complexity_score": 5,
        "error_message": execution_data.get("error"),
        "variables": execution_data.get("variables", {}),
        "trace_id": f"trace-{uuid4()}"
    }
    
    return mock_execution


@executions_router.post("/{execution_id}/favorite")
async def toggle_favorite(execution_id: str):
    """Toggle favorite status for an execution."""
    
    # Mock successful toggle
    return {
        "id": execution_id,
        "favorite": True,
        "message": "Favorite status toggled"
    }


@executions_router.delete("/{execution_id}")
async def delete_execution(execution_id: str):
    """Delete a query execution."""
    
    # Mock successful deletion
    return {"message": "Execution deleted successfully"}


@executions_router.post("/clear")
async def clear_history(endpoint_id: Optional[str] = QueryParam(None)):
    """Clear query history."""
    
    # Mock successful clear
    cleared_count = 150 if endpoint_id else 1247
    return {"message": f"Cleared {cleared_count} execution records"}