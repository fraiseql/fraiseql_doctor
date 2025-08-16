# Phase 4: Query Management System
**Agent: Business Logic Developer**

## Objective
Create a comprehensive query management and execution system that handles CRUD operations, validation, scheduling, and performance analysis for FraiseQL queries across multiple endpoints.

## Requirements

### Core Services Architecture

#### 1. Query Service
```python
"""Query management service with validation and storage."""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.schemas.query import QueryCreate, QueryUpdate, QueryResponse
from fraiseql_doctor.core.exceptions import (
    QueryNotFoundError,
    QueryValidationError,
    DuplicateQueryError
)
from fraiseql_doctor.services.validation import QueryValidator


class QueryService:
    """Service for managing FraiseQL queries."""
    
    def __init__(self, db_session: AsyncSession, validator: QueryValidator):
        self.db = db_session
        self.validator = validator
    
    async def create_query(self, query_data: QueryCreate) -> QueryResponse:
        """Create a new query with validation."""
        # Validate query syntax and complexity
        validation_result = await self.validator.validate_query(
            query_data.query_text,
            query_data.variables
        )
        
        if not validation_result.is_valid:
            raise QueryValidationError(
                f"Query validation failed: {validation_result.errors}"
            )
        
        # Check for duplicate names
        existing = await self._get_query_by_name(query_data.name)
        if existing:
            raise DuplicateQueryError(f"Query with name '{query_data.name}' already exists")
        
        # Create query with validation metadata
        query = Query(
            name=query_data.name,
            description=query_data.description,
            query_text=query_data.query_text,
            variables=query_data.variables,
            expected_complexity_score=validation_result.complexity_score,
            tags=query_data.tags,
            created_by=query_data.created_by,
            metadata={
                "validation": validation_result.dict(),
                "created_via": "api"
            }
        )
        
        self.db.add(query)
        await self.db.commit()
        await self.db.refresh(query)
        
        return QueryResponse.from_orm(query)
    
    async def get_query(self, query_id: UUID) -> QueryResponse:
        """Get query by ID with execution statistics."""
        query = await self.db.get(Query, query_id)
        if not query:
            raise QueryNotFoundError(f"Query {query_id} not found")
        
        # Load recent execution statistics
        recent_executions = await self._get_recent_executions(query_id, limit=10)
        
        response = QueryResponse.from_orm(query)
        response.recent_executions = recent_executions
        response.performance_stats = await self._calculate_performance_stats(query_id)
        
        return response
    
    async def list_queries(
        self,
        tags: List[str] | None = None,
        is_active: bool | None = None,
        created_by: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QueryResponse]:
        """List queries with filtering."""
        stmt = select(Query)
        
        # Apply filters
        if tags:
            stmt = stmt.where(Query.tags.contains(tags))
        if is_active is not None:
            stmt = stmt.where(Query.is_active == is_active)
        if created_by:
            stmt = stmt.where(Query.created_by == created_by)
        
        stmt = stmt.offset(offset).limit(limit).order_by(Query.created_at.desc())
        
        result = await self.db.execute(stmt)
        queries = result.scalars().all()
        
        return [QueryResponse.from_orm(q) for q in queries]
    
    async def update_query(self, query_id: UUID, update_data: QueryUpdate) -> QueryResponse:
        """Update existing query with revalidation."""
        query = await self.db.get(Query, query_id)
        if not query:
            raise QueryNotFoundError(f"Query {query_id} not found")
        
        # Validate if query text changed
        if update_data.query_text and update_data.query_text != query.query_text:
            validation_result = await self.validator.validate_query(
                update_data.query_text,
                update_data.variables or query.variables
            )
            
            if not validation_result.is_valid:
                raise QueryValidationError(
                    f"Query validation failed: {validation_result.errors}"
                )
            
            query.expected_complexity_score = validation_result.complexity_score
            query.metadata["validation"] = validation_result.dict()
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(query, field, value)
        
        query.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(query)
        
        return QueryResponse.from_orm(query)
    
    async def delete_query(self, query_id: UUID) -> bool:
        """Delete query and all related executions."""
        query = await self.db.get(Query, query_id)
        if not query:
            raise QueryNotFoundError(f"Query {query_id} not found")
        
        await self.db.delete(query)
        await self.db.commit()
        
        return True
    
    async def _get_query_by_name(self, name: str) -> Query | None:
        """Get query by name."""
        stmt = select(Query).where(Query.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_recent_executions(self, query_id: UUID, limit: int = 10) -> List[Dict]:
        """Get recent executions for query."""
        stmt = (
            select(Execution)
            .where(Execution.fk_query == query_id)
            .order_by(Execution.execution_start.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        executions = result.scalars().all()
        
        return [
            {
                "execution_id": str(e.pk_execution),
                "status": e.status,
                "response_time_ms": e.response_time_ms,
                "execution_start": e.execution_start.isoformat(),
                "error_message": e.error_message
            }
            for e in executions
        ]
    
    async def _calculate_performance_stats(self, query_id: UUID) -> Dict[str, Any]:
        """Calculate performance statistics for query."""
        # This would include complex aggregation queries
        # Simplified version for brevity
        return {
            "avg_response_time_ms": 0,
            "success_rate": 0.0,
            "total_executions": 0
        }
```

#### 2. Execution Service
```python
"""Query execution service with comprehensive tracking."""
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient, GraphQLResponse
from fraiseql_doctor.services.metrics import MetricsCollector, QueryMetrics
from fraiseql_doctor.core.exceptions import ExecutionError


class ExecutionService:
    """Service for executing FraiseQL queries."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        client_factory: Callable[[Endpoint], FraiseQLClient],
        metrics_collector: MetricsCollector
    ):
        self.db = db_session
        self.client_factory = client_factory
        self.metrics = metrics_collector
    
    async def execute_query(
        self,
        query_id: UUID,
        endpoint_id: UUID,
        variables: Dict[str, Any] | None = None,
        timeout: int | None = None
    ) -> Dict[str, Any]:
        """Execute a single query against an endpoint."""
        # Load query and endpoint
        query = await self.db.get(Query, query_id)
        endpoint = await self.db.get(Endpoint, endpoint_id)
        
        if not query or not endpoint:
            raise ExecutionError("Query or endpoint not found")
        
        if not query.is_active or not endpoint.is_active:
            raise ExecutionError("Query or endpoint is not active")
        
        # Create execution record
        execution = Execution(
            fk_query=query_id,
            fk_endpoint=endpoint_id,
            status="pending",
            variables_used=variables or query.variables,
            execution_context={
                "timeout": timeout,
                "user_agent": "fraiseql-doctor",
                "version": "0.1.0"
            }
        )
        
        self.db.add(execution)
        await self.db.commit()
        
        try:
            # Execute query
            client = self.client_factory(endpoint)
            response = await client.execute_query(
                query.query_text,
                variables or query.variables,
                timeout=timeout
            )
            
            # Update execution with results
            execution.execution_end = datetime.utcnow()
            execution.response_time_ms = response.response_time_ms
            execution.actual_complexity_score = response.complexity_score
            execution.response_size_bytes = len(str(response.data or ""))
            
            if response.errors:
                execution.status = "error"
                execution.error_message = str(response.errors)
                execution.error_code = "GRAPHQL_ERROR"
            else:
                execution.status = "success"
                execution.response_data = response.data
            
            # Record metrics
            self.metrics.record_query(QueryMetrics(
                query_id=str(query_id),
                endpoint_id=str(endpoint_id),
                execution_time_ms=response.response_time_ms,
                response_size_bytes=execution.response_size_bytes,
                complexity_score=response.complexity_score,
                success=execution.status == "success",
                error_message=execution.error_message
            ))
            
            await self.db.commit()
            
            return {
                "execution_id": str(execution.pk_execution),
                "status": execution.status,
                "response_time_ms": execution.response_time_ms,
                "data": execution.response_data,
                "errors": response.errors,
                "complexity_score": execution.actual_complexity_score
            }
            
        except Exception as e:
            # Handle execution failure
            execution.execution_end = datetime.utcnow()
            execution.status = "error"
            execution.error_message = str(e)
            execution.error_code = type(e).__name__
            
            await self.db.commit()
            
            raise ExecutionError(f"Query execution failed: {e}") from e
    
    async def execute_batch(
        self,
        executions: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Execute multiple queries concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(exec_data: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute_query(
                    query_id=exec_data["query_id"],
                    endpoint_id=exec_data["endpoint_id"],
                    variables=exec_data.get("variables"),
                    timeout=exec_data.get("timeout")
                )
        
        tasks = [execute_single(exec_data) for exec_data in executions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "execution_id": None,
                    "status": "error",
                    "error_message": str(result),
                    "query_id": str(executions[i]["query_id"]),
                    "endpoint_id": str(executions[i]["endpoint_id"])
                })
            else:
                formatted_results.append(result)
        
        return formatted_results
```

#### 3. Health Check Service
```python
"""Health monitoring service for FraiseQL endpoints."""
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.health_check import HealthCheck
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient


class HealthCheckService:
    """Service for monitoring FraiseQL endpoint health."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        client_factory: Callable[[Endpoint], FraiseQLClient]
    ):
        self.db = db_session
        self.client_factory = client_factory
    
    async def check_endpoint_health(self, endpoint_id: UUID) -> Dict[str, Any]:
        """Perform comprehensive health check on endpoint."""
        endpoint = await self.db.get(Endpoint, endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        health_check = HealthCheck(
            fk_endpoint=endpoint_id,
            check_time=datetime.utcnow()
        )
        
        try:
            client = self.client_factory(endpoint)
            
            # Introspection query to check basic connectivity
            introspection_query = """
                query IntrospectionQuery {
                    __schema {
                        queryType { name }
                        mutationType { name }
                        subscriptionType { name }
                    }
                }
            """
            
            start_time = datetime.utcnow()
            response = await client.execute_query(introspection_query)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Analyze response
            if response.data and response.data.get("__schema"):
                health_check.is_healthy = True
                health_check.response_time_ms = int(response_time)
                health_check.status_code = 200
                
                schema_data = response.data["__schema"]
                health_check.available_operations = [
                    op for op in ["query", "mutation", "subscription"]
                    if schema_data.get(f"{op}Type")
                ]
                
                # Extract version if available in extensions
                if response.extensions:
                    health_check.endpoint_version = response.extensions.get("version")
                
                health_check.performance_metrics = {
                    "response_time_ms": int(response_time),
                    "complexity_supported": response.complexity_score is not None,
                    "caching_enabled": response.cached,
                    "extensions_available": bool(response.extensions)
                }
            else:
                health_check.is_healthy = False
                health_check.error_message = "Invalid schema response"
                
        except Exception as e:
            health_check.is_healthy = False
            health_check.error_message = str(e)
            health_check.response_time_ms = None
        
        # Update endpoint last health check
        endpoint.last_health_check = health_check.check_time
        
        self.db.add(health_check)
        await self.db.commit()
        
        return {
            "endpoint_id": str(endpoint_id),
            "is_healthy": health_check.is_healthy,
            "response_time_ms": health_check.response_time_ms,
            "error_message": health_check.error_message,
            "available_operations": health_check.available_operations,
            "performance_metrics": health_check.performance_metrics,
            "check_time": health_check.check_time.isoformat()
        }
    
    async def check_all_endpoints(self) -> List[Dict[str, Any]]:
        """Check health of all active endpoints."""
        stmt = select(Endpoint).where(Endpoint.is_active == True)
        result = await self.db.execute(stmt)
        endpoints = result.scalars().all()
        
        tasks = [
            self.check_endpoint_health(endpoint.pk_endpoint)
            for endpoint in endpoints
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "endpoint_id": str(endpoints[i].pk_endpoint),
                    "is_healthy": False,
                    "error_message": str(result),
                    "check_time": datetime.utcnow().isoformat()
                })
            else:
                formatted_results.append(result)
        
        return formatted_results
    
    async def get_health_history(
        self,
        endpoint_id: UUID,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get health check history for endpoint."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = (
            select(HealthCheck)
            .where(
                HealthCheck.fk_endpoint == endpoint_id,
                HealthCheck.check_time >= cutoff_time
            )
            .order_by(HealthCheck.check_time.desc())
        )
        
        result = await self.db.execute(stmt)
        health_checks = result.scalars().all()
        
        return [
            {
                "check_time": hc.check_time.isoformat(),
                "is_healthy": hc.is_healthy,
                "response_time_ms": hc.response_time_ms,
                "error_message": hc.error_message,
                "performance_metrics": hc.performance_metrics
            }
            for hc in health_checks
        ]
```

#### 4. Scheduling Service
```python
"""Query scheduling service with cron support."""
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import asyncio
from croniter import croniter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from fraiseql_doctor.models.schedule import Schedule
from fraiseql_doctor.services.execution import ExecutionService


class SchedulingService:
    """Service for scheduling and running FraiseQL queries."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        execution_service: ExecutionService
    ):
        self.db = db_session
        self.execution_service = execution_service
        self._running = False
    
    async def create_schedule(
        self,
        query_id: UUID,
        endpoint_id: UUID,
        name: str,
        cron_expression: str,
        notification_config: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Create a new query schedule."""
        # Validate cron expression
        try:
            cron = croniter(cron_expression)
            next_run = cron.get_next(datetime)
        except Exception as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        schedule = Schedule(
            fk_query=query_id,
            fk_endpoint=endpoint_id,
            name=name,
            cron_expression=cron_expression,
            next_run=next_run,
            notification_config=notification_config or {}
        )
        
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)
        
        return {
            "schedule_id": str(schedule.pk_schedule),
            "name": schedule.name,
            "cron_expression": schedule.cron_expression,
            "next_run": schedule.next_run.isoformat(),
            "is_active": schedule.is_active
        }
    
    async def start_scheduler(self) -> None:
        """Start the background scheduler."""
        self._running = True
        
        while self._running:
            try:
                await self._process_due_schedules()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                # Log error but continue running
                print(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def stop_scheduler(self) -> None:
        """Stop the background scheduler."""
        self._running = False
    
    async def _process_due_schedules(self) -> None:
        """Process schedules that are due to run."""
        now = datetime.utcnow()
        
        stmt = (
            select(Schedule)
            .where(
                Schedule.is_active == True,
                Schedule.next_run <= now
            )
        )
        
        result = await self.db.execute(stmt)
        due_schedules = result.scalars().all()
        
        for schedule in due_schedules:
            try:
                # Execute the scheduled query
                execution_result = await self.execution_service.execute_query(
                    query_id=schedule.fk_query,
                    endpoint_id=schedule.fk_endpoint
                )
                
                # Update schedule statistics
                schedule.last_run = now
                schedule.run_count += 1
                
                if execution_result["status"] == "error":
                    schedule.failure_count += 1
                    
                    # Disable schedule if too many failures
                    if schedule.failure_count >= schedule.max_failures:
                        schedule.is_active = False
                else:
                    # Reset failure count on success
                    schedule.failure_count = 0
                
                # Calculate next run time
                cron = croniter(schedule.cron_expression, now)
                schedule.next_run = cron.get_next(datetime)
                
                await self.db.commit()
                
            except Exception as e:
                # Handle schedule execution failure
                schedule.failure_count += 1
                schedule.last_run = now
                
                if schedule.failure_count >= schedule.max_failures:
                    schedule.is_active = False
                
                await self.db.commit()
                print(f"Schedule {schedule.pk_schedule} failed: {e}")
```

### Data Import/Export

#### 5. Import/Export Service
```python
"""Service for importing and exporting query collections."""
import json
import yaml
from typing import Dict, Any, List
from uuid import UUID
from pathlib import Path

from fraiseql_doctor.schemas.query import QueryCreate
from fraiseql_doctor.services.query import QueryService


class ImportExportService:
    """Service for importing and exporting FraiseQL queries."""
    
    def __init__(self, query_service: QueryService):
        self.query_service = query_service
    
    async def export_queries(
        self,
        query_ids: List[UUID] | None = None,
        format: str = "json"
    ) -> str:
        """Export queries to JSON or YAML format."""
        if query_ids:
            queries = []
            for query_id in query_ids:
                query = await self.query_service.get_query(query_id)
                queries.append(query)
        else:
            queries = await self.query_service.list_queries()
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "queries": [
                {
                    "name": q.name,
                    "description": q.description,
                    "query_text": q.query_text,
                    "variables": q.variables,
                    "tags": q.tags,
                    "metadata": q.metadata
                }
                for q in queries
            ]
        }
        
        if format.lower() == "yaml":
            return yaml.dump(export_data, default_flow_style=False)
        else:
            return json.dumps(export_data, indent=2)
    
    async def import_queries(
        self,
        data: str,
        format: str = "json",
        created_by: str | None = None
    ) -> List[Dict[str, Any]]:
        """Import queries from JSON or YAML format."""
        if format.lower() == "yaml":
            import_data = yaml.safe_load(data)
        else:
            import_data = json.loads(data)
        
        results = []
        
        for query_data in import_data.get("queries", []):
            try:
                query_create = QueryCreate(
                    name=query_data["name"],
                    description=query_data.get("description"),
                    query_text=query_data["query_text"],
                    variables=query_data.get("variables", {}),
                    tags=query_data.get("tags", []),
                    created_by=created_by,
                    metadata=query_data.get("metadata", {})
                )
                
                query = await self.query_service.create_query(query_create)
                
                results.append({
                    "name": query.name,
                    "status": "success",
                    "query_id": str(query.pk_query)
                })
                
            except Exception as e:
                results.append({
                    "name": query_data.get("name", "unknown"),
                    "status": "error",
                    "error": str(e)
                })
        
        return results
```

### Success Criteria
- [x] Complete CRUD operations for queries with validation
- [x] Robust query execution service with error handling
- [x] Health monitoring system for endpoints
- [x] Scheduling system with cron support
- [x] Import/export functionality for query collections
- [x] Performance metrics collection and analysis
- [x] Batch execution capabilities
- [x] Comprehensive error handling and logging

### Handoff Notes for Next Phase
- CLI should use these services for all operations
- Implement proper dependency injection for services
- Add comprehensive logging to all service methods
- Consider implementing caching for frequently accessed queries
- Ensure all services handle database connection failures gracefully
- Add proper transaction management for complex operations