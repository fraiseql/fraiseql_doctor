"""Execution API schemas."""

from typing import Any

from pydantic import BaseModel


class ExecutionResponse(BaseModel):
    """Response schema for a single execution."""

    id: str
    endpoint_id: str
    query_id: str
    status: str
    operation_name: str | None = None
    started_at: str
    completed_at: str | None = None
    response_time_ms: int | None = None
    complexity_score: int | None = None
    error_message: str | None = None
    variables: dict[str, Any] | None = None
    trace_id: str | None = None


class ExecutionListResponse(BaseModel):
    """Response schema for execution list with pagination."""

    executions: list[ExecutionResponse]
    total: int
    limit: int
    offset: int


class CreateExecutionRequest(BaseModel):
    """Request schema for creating a new execution."""

    endpoint_id: str
    query: str
    variables: dict[str, Any] | None = None
    execution_time: int | None = None
    success: bool = True
    result: dict[str, Any] | None = None
    status_code: int | None = None
    error: str | None = None


class UpdateExecutionRequest(BaseModel):
    """Request schema for updating an execution."""

    favorite: bool | None = None
