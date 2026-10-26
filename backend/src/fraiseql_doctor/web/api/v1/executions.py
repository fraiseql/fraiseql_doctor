"""Query execution history API endpoints - Maps to Query History frontend feature."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.models.query import Query as QueryModel

from ...core.database import get_database_session
from .schemas.executions import (
    ExecutionListResponse,
    ExecutionResponse,
    ExecutionStatsResponse,
)

executions_router = APIRouter()


@executions_router.get("/", response_model=ExecutionListResponse)
async def get_query_history(
    endpoint_id: str | None = Query(None, description="Filter by endpoint ID"),
    success: bool | None = Query(None, description="Filter by success status"),
    search: str | None = Query(None, description="Search in query text and operation names"),
    favorite: bool | None = Query(None, description="Filter by favorite status"),
    from_date: datetime | None = Query(None, description="Filter from date"),
    to_date: datetime | None = Query(None, description="Filter to date"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_database_session),
) -> ExecutionListResponse:
    """Get query execution history with filtering and pagination.

    This endpoint maps to the frontend Query History feature.
    """
    # Build the query
    query = select(Execution)

    # Apply filters
    conditions = []

    if endpoint_id:
        conditions.append(Execution.endpoint_id == UUID(endpoint_id))

    if success is not None:
        if success:
            conditions.append(Execution.status == "success")
        else:
            conditions.append(Execution.status != "success")

    if search:
        # Search in query text and endpoint names
        search_conditions = []
        search_conditions.append(Execution.query.has(QueryModel.query_text.ilike(f"%{search}%")))
        search_conditions.append(Execution.query.has(QueryModel.name.ilike(f"%{search}%")))
        search_conditions.append(Execution.endpoint.has(Endpoint.name.ilike(f"%{search}%")))
        conditions.append(or_(*search_conditions))

    if favorite is not None and favorite:
        # For now, assume favorites are stored in query metadata
        conditions.append(
            Execution.query.has(
                QueryModel.query_metadata.op("->>")("favorite").cast(db.bind.dialect.BOOLEAN)
                == True
            )
        )

    if from_date:
        conditions.append(Execution.started_at >= from_date)

    if to_date:
        conditions.append(Execution.started_at <= to_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Apply ordering (newest first)
    query = query.order_by(Execution.started_at.desc())

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    executions = result.scalars().all()

    # Get total count for pagination
    count_query = select(func.count(Execution.pk_execution))
    if conditions:
        count_query = count_query.where(and_(*conditions))

    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    # Convert to response format
    execution_responses = []
    for execution in executions:
        execution_responses.append(ExecutionResponse.from_execution(execution))

    return ExecutionListResponse(
        executions=execution_responses, total=total_count, limit=limit, offset=offset
    )


@executions_router.get("/stats", response_model=ExecutionStatsResponse)
async def get_query_history_stats(
    endpoint_id: str | None = Query(None, description="Filter by endpoint ID"),
    from_date: datetime | None = Query(None, description="Stats from date"),
    to_date: datetime | None = Query(None, description="Stats to date"),
    db: AsyncSession = Depends(get_database_session),
) -> ExecutionStatsResponse:
    """Get query execution statistics.

    Maps to the stats display in the Query History frontend.
    """
    # Build base conditions
    conditions = []

    if endpoint_id:
        conditions.append(Execution.endpoint_id == UUID(endpoint_id))

    if from_date:
        conditions.append(Execution.started_at >= from_date)

    if to_date:
        conditions.append(Execution.started_at <= to_date)

    where_clause = and_(*conditions) if conditions else True

    # Get total queries
    total_query = select(func.count(Execution.pk_execution)).where(where_clause)
    total_result = await db.execute(total_query)
    total_queries = total_result.scalar() or 0

    # Get successful queries
    success_query = select(func.count(Execution.pk_execution)).where(
        and_(where_clause, Execution.status == "success")
    )
    success_result = await db.execute(success_query)
    successful_queries = success_result.scalar() or 0

    # Get average response time
    avg_time_query = select(func.avg(Execution.response_time_ms)).where(
        and_(where_clause, Execution.status == "success")
    )
    avg_time_result = await db.execute(avg_time_query)
    avg_response_time = avg_time_result.scalar() or 0.0

    return ExecutionStatsResponse(
        total_queries=total_queries,
        successful_queries=successful_queries,
        failed_queries=total_queries - successful_queries,
        average_response_time=float(avg_response_time),
    )


@executions_router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution_by_id(
    execution_id: UUID, db: AsyncSession = Depends(get_database_session)
) -> ExecutionResponse:
    """Get a specific execution by ID."""
    query = (
        select(Execution)
        .options(selectinload(Execution.query), selectinload(Execution.endpoint))
        .where(Execution.pk_execution == execution_id)
    )

    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionResponse.from_execution(execution)


@executions_router.post("/{execution_id}/favorite")
async def toggle_execution_favorite(
    execution_id: UUID, db: AsyncSession = Depends(get_database_session)
) -> dict[str, str]:
    """Toggle favorite status of an execution.

    Maps to the favorite functionality in Query History frontend.
    """
    # Get the execution and its query
    query = (
        select(Execution)
        .options(selectinload(Execution.query))
        .where(Execution.pk_execution == execution_id)
    )
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Toggle favorite in query metadata
    current_metadata = execution.query.query_metadata or {}
    current_favorite = current_metadata.get("favorite", False)
    current_metadata["favorite"] = not current_favorite
    execution.query.query_metadata = current_metadata

    await db.commit()

    return {
        "message": f"Execution {'added to' if not current_favorite else 'removed from'} favorites",
        "favorite": not current_favorite,
    }


@executions_router.delete("/{execution_id}")
async def delete_execution(
    execution_id: UUID, db: AsyncSession = Depends(get_database_session)
) -> dict[str, str]:
    """Delete an execution from history.

    Maps to the delete functionality in Query History frontend.
    """
    query = select(Execution).where(Execution.pk_execution == execution_id)
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    await db.delete(execution)
    await db.commit()

    return {"message": "Execution deleted successfully"}


@executions_router.post("/clear")
async def clear_all_executions(
    endpoint_id: str | None = Query(
        None, description="Clear only executions for specific endpoint"
    ),
    db: AsyncSession = Depends(get_database_session),
) -> dict[str, str]:
    """Clear all executions (with optional endpoint filter).

    Maps to the "Clear All" functionality in Query History frontend.
    """
    if endpoint_id:
        # Clear executions for specific endpoint
        query = select(Execution).where(Execution.fk_endpoint == UUID(endpoint_id))
        result = await db.execute(query)
        executions = result.scalars().all()

        for execution in executions:
            await db.delete(execution)

        message = f"Cleared {len(executions)} executions for endpoint {endpoint_id}"
    else:
        # Clear all executions
        query = select(Execution)
        result = await db.execute(query)
        executions = result.scalars().all()

        for execution in executions:
            await db.delete(execution)

        message = f"Cleared {len(executions)} executions from history"

    await db.commit()
    return {"message": message}
