"""Execution API schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionResponse(BaseModel):
    """Response schema for a single execution."""
    
    id: str
    endpoint_id: str
    query_id: str
    status: str
    operation_name: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    response_time_ms: Optional[int] = None
    complexity_score: Optional[int] = None
    error_message: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None


class ExecutionListResponse(BaseModel):
    """Response schema for execution list with pagination."""
    
    executions: List[ExecutionResponse]
    total: int
    limit: int
    offset: int


class CreateExecutionRequest(BaseModel):
    """Request schema for creating a new execution."""
    
    endpoint_id: str
    query: str
    variables: Optional[Dict[str, Any]] = None
    execution_time: Optional[int] = None
    success: bool = True
    result: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None
    error: Optional[str] = None


class UpdateExecutionRequest(BaseModel):
    """Request schema for updating an execution."""
    
    favorite: Optional[bool] = None