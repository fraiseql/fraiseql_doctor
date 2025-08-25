"""Pydantic schemas for execution/query history API responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from fraiseql_doctor.models.execution import Execution


class ExecutionEndpointInfo(BaseModel):
    """Endpoint information for execution response."""

    id: UUID
    name: str
    url: str


class ExecutionQueryInfo(BaseModel):
    """Query information for execution response."""

    id: UUID
    name: str
    query_text: str
    variables: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    favorite: bool = False


class ExecutionResponse(BaseModel):
    """Response schema for query execution history.

    Maps to QueryHistoryEntry in frontend.
    """

    id: UUID = Field(..., description="Execution ID")
    query: ExecutionQueryInfo
    endpoint: ExecutionEndpointInfo
    timestamp: datetime = Field(..., description="Execution start time")
    execution_time: int | None = Field(None, description="Response time in milliseconds")
    success: bool = Field(..., description="Whether execution was successful")
    status: str = Field(..., description="Execution status (success, error, timeout, etc.)")
    status_code: int | None = Field(None, description="HTTP status code if available")
    error: str | None = Field(None, description="Error message if failed")
    result: dict[str, Any] | None = Field(None, description="Query result data")
    variables: dict[str, Any] = Field(default_factory=dict, description="Variables used")
    tags: list[str] = Field(default_factory=list, description="Query tags")
    favorite: bool = Field(False, description="Whether query is favorited")

    @classmethod
    def from_execution(cls, execution: Execution) -> "ExecutionResponse":
        """Create ExecutionResponse from Execution model."""
        # Extract favorite status from query metadata
        favorite = False
        if execution.query and execution.query.query_metadata:
            favorite = execution.query.query_metadata.get("favorite", False)

        # Map status to success boolean
        success = execution.status == "success"

        # Create query info
        query_info = ExecutionQueryInfo(
            id=execution.query.pk_query,
            name=execution.query.name,
            query_text=execution.query.query_text,
            variables=execution.query.variables or {},
            tags=execution.query.tags or [],
            favorite=favorite,
        )

        # Create endpoint info
        endpoint_info = ExecutionEndpointInfo(
            id=execution.endpoint.pk_endpoint,
            name=execution.endpoint.name,
            url=execution.endpoint.url,
        )

        return cls(
            id=execution.pk_execution,
            query=query_info,
            endpoint=endpoint_info,
            timestamp=execution.execution_start,
            execution_time=execution.response_time_ms,
            success=success,
            status=execution.status,
            status_code=None,  # Could extract from response_data if available
            error=execution.error_message,
            result=execution.response_data,
            variables=execution.variables_used or {},
            tags=execution.query.tags or [],
            favorite=favorite,
        )


class ExecutionListResponse(BaseModel):
    """Response schema for paginated execution list."""

    executions: list[ExecutionResponse]
    total: int = Field(..., description="Total number of executions matching filters")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")


class ExecutionStatsResponse(BaseModel):
    """Response schema for execution statistics."""

    total_queries: int = Field(..., description="Total number of queries executed")
    successful_queries: int = Field(..., description="Number of successful queries")
    failed_queries: int = Field(..., description="Number of failed queries")
    average_response_time: float = Field(..., description="Average response time in milliseconds")


class QueryHistoryFilter(BaseModel):
    """Filter parameters for query history."""

    endpoint_id: str | None = None
    success: bool | None = None
    search_term: str | None = None
    favorite: bool | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class QueryHistoryExportOptions(BaseModel):
    """Export options for query history."""

    format: str = Field(..., description="Export format (json, csv, graphql)")
    include_results: bool = Field(True, description="Include query results in export")
    include_variables: bool = Field(True, description="Include variables in export")
    filter: QueryHistoryFilter | None = None
