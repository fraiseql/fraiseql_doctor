"""
Query Execution Manager

Orchestrates GraphQL query execution with:
- Scheduled execution with cron-like scheduling
- Batch processing for efficient resource usage
- Concurrent execution with backpressure control
- Execution result tracking and error handling
- Performance monitoring and optimization
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import json
from croniter import croniter

from ..models.execution import Execution
from ..models.query import Query
from ..models.endpoint import Endpoint
from ..services.fraiseql_client import FraiseQLClient, GraphQLExecutionError, NetworkError
from .query_collection import QueryCollectionManager, QueryStatus, QueryPriority


logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Query execution status."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class BatchMode(Enum):
    """Batch execution modes."""
    SEQUENTIAL = "sequential"  # Execute queries one by one
    PARALLEL = "parallel"      # Execute all queries concurrently
    PRIORITY = "priority"      # Execute by priority order
    ADAPTIVE = "adaptive"      # Adjust based on system load


@dataclass
class ExecutionConfig:
    """Configuration for query execution."""
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5
    max_concurrent: int = 10
    batch_size: int = 50
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    priority_weights: Dict[QueryPriority, int] = field(default_factory=lambda: {
        QueryPriority.LOW: 1,
        QueryPriority.MEDIUM: 2, 
        QueryPriority.HIGH: 3,
        QueryPriority.CRITICAL: 5
    })


@dataclass
class ExecutionResult:
    """Result of a single query execution."""
    execution_id: UUID
    query_id: UUID
    endpoint_id: UUID
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    success: bool = False
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    complexity_score: Optional[float] = None
    response_size: Optional[int] = None
    cache_hit: bool = False
    variables: Optional[Dict[str, Any]] = None


@dataclass
class BatchExecutionResult:
    """Result of a batch execution."""
    batch_id: UUID
    total_queries: int
    successful: int
    failed: int
    cancelled: int
    total_time: float
    results: List[ExecutionResult]
    errors: List[str] = field(default_factory=list)


@dataclass
class ScheduledExecution:
    """Scheduled query execution configuration."""
    id: UUID
    query_id: UUID
    cron_expression: str
    endpoint_id: UUID
    config: ExecutionConfig
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None


class QueryExecutionManager:
    """
    Manages GraphQL query execution with advanced scheduling and batch processing.
    
    Features:
    - Cron-based scheduling
    - Concurrent execution with backpressure
    - Batch processing modes
    - Result tracking and storage
    - Performance monitoring
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        db_session,
        client_factory: Callable[[Endpoint], FraiseQLClient],
        collection_manager: QueryCollectionManager,
        config: ExecutionConfig = None
    ):
        self.db_session = db_session
        self.client_factory = client_factory
        self.collection_manager = collection_manager
        self.config = config or ExecutionConfig()
        
        # Execution state
        self._running_executions: Dict[UUID, asyncio.Task] = {}
        self._scheduled_executions: Dict[UUID, ScheduledExecution] = {}
        self._execution_semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._scheduler_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Metrics
        self._execution_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        # Thread pool for CPU-bound operations
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
    
    # Single Query Execution
    
    async def execute_query(
        self,
        query_id: UUID,
        endpoint_id: UUID,
        variables: Optional[Dict[str, Any]] = None,
        config_override: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Execute a single query with comprehensive result tracking.
        
        Args:
            query_id: Query to execute
            endpoint_id: Target endpoint
            variables: Query variables override
            config_override: Execution configuration override
            
        Returns:
            ExecutionResult with complete execution details
        """
        execution_id = uuid4()
        config = config_override or self.config
        started_at = datetime.now(timezone.utc)
        
        # Get query and endpoint
        query = await self.collection_manager.get_query(query_id)
        if not query:
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                error_message="Query not found",
                error_code="QUERY_NOT_FOUND",
                variables=variables
            )
        
        endpoint = await self.db_session.get(Endpoint, endpoint_id)
        if not endpoint:
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                error_message="Endpoint not found",
                error_code="ENDPOINT_NOT_FOUND",
                variables=variables
            )
        
        # Create client
        client = self.client_factory(endpoint)
        
        # Use query variables or provided override
        final_variables = variables or query.variables
        
        logger.info(f"Starting execution {execution_id} for query {query.name}")
        
        try:
            async with self._execution_semaphore:
                # Execute query with timeout
                result_data = await asyncio.wait_for(
                    client.execute_query(query.query_text, final_variables),
                    timeout=config.timeout_seconds
                )
                
                completed_at = datetime.now(timezone.utc)
                execution_time = (completed_at - started_at).total_seconds()
                
                # Calculate response size
                response_size = len(json.dumps(result_data)) if result_data else 0
                
                # Check for GraphQL errors
                if "errors" in result_data:
                    error_messages = [err.get("message", "Unknown error") for err in result_data["errors"]]
                    return ExecutionResult(
                        execution_id=execution_id,
                        query_id=query_id,
                        endpoint_id=endpoint_id,
                        status=ExecutionStatus.FAILED,
                        started_at=started_at,
                        completed_at=completed_at,
                        execution_time=execution_time,
                        error_message="; ".join(error_messages),
                        error_code="GRAPHQL_ERROR",
                        response_size=response_size,
                        variables=final_variables
                    )
                
                # Successful execution
                result = ExecutionResult(
                    execution_id=execution_id,
                    query_id=query_id,
                    endpoint_id=endpoint_id,
                    status=ExecutionStatus.COMPLETED,
                    started_at=started_at,
                    completed_at=completed_at,
                    execution_time=execution_time,
                    success=True,
                    result_data=result_data,
                    complexity_score=query.expected_complexity_score,
                    response_size=response_size,
                    cache_hit=result_data.get("_cache_hit", False),
                    variables=final_variables
                )
                
                # Update metrics
                self._update_execution_metrics(result)
                
                # Store execution record
                await self._store_execution_result(result)
                
                logger.info(f"Completed execution {execution_id} in {execution_time:.2f}s")
                return result
                
        except asyncio.TimeoutError:
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.TIMEOUT,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=f"Query timed out after {config.timeout_seconds}s",
                error_code="TIMEOUT",
                variables=final_variables
            )
            
        except GraphQLExecutionError as e:
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=str(e),
                error_code="GRAPHQL_EXECUTION_ERROR",
                variables=final_variables
            )
            
        except NetworkError as e:
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=f"Network error: {e}",
                error_code="NETWORK_ERROR",
                variables=final_variables
            )
            
        except Exception as e:
            logger.exception(f"Unexpected error in execution {execution_id}")
            return ExecutionResult(
                execution_id=execution_id,
                query_id=query_id,
                endpoint_id=endpoint_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                error_message=f"Unexpected error: {e}",
                error_code="UNEXPECTED_ERROR",
                variables=variables
            )
    
    # Batch Execution
    
    async def execute_batch(
        self,
        query_ids: List[UUID],
        endpoint_id: UUID,
        mode: BatchMode = BatchMode.PARALLEL,
        variables_map: Optional[Dict[UUID, Dict[str, Any]]] = None,
        config_override: Optional[ExecutionConfig] = None
    ) -> BatchExecutionResult:
        """
        Execute multiple queries in batch with different execution modes.
        
        Args:
            query_ids: List of queries to execute
            endpoint_id: Target endpoint
            mode: Batch execution mode
            variables_map: Query-specific variables
            config_override: Execution configuration override
            
        Returns:
            BatchExecutionResult with aggregated results
        """
        batch_id = uuid4()
        config = config_override or self.config
        batch_start = datetime.now(timezone.utc)
        
        logger.info(f"Starting batch execution {batch_id} with {len(query_ids)} queries in {mode.value} mode")
        
        # Prepare execution tasks
        variables_map = variables_map or {}
        
        if mode == BatchMode.SEQUENTIAL:
            results = await self._execute_sequential(query_ids, endpoint_id, variables_map, config)
        elif mode == BatchMode.PARALLEL:
            results = await self._execute_parallel(query_ids, endpoint_id, variables_map, config)
        elif mode == BatchMode.PRIORITY:
            results = await self._execute_by_priority(query_ids, endpoint_id, variables_map, config)
        elif mode == BatchMode.ADAPTIVE:
            results = await self._execute_adaptive(query_ids, endpoint_id, variables_map, config)
        else:
            raise ValueError(f"Unknown batch mode: {mode}")
        
        batch_end = datetime.now(timezone.utc)
        total_time = (batch_end - batch_start).total_seconds()
        
        # Aggregate results
        successful = len([r for r in results if r.success])
        failed = len([r for r in results if not r.success and r.status == ExecutionStatus.FAILED])
        cancelled = len([r for r in results if r.status == ExecutionStatus.CANCELLED])
        
        batch_result = BatchExecutionResult(
            batch_id=batch_id,
            total_queries=len(query_ids),
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            total_time=total_time,
            results=results
        )
        
        logger.info(f"Batch {batch_id} completed: {successful} successful, {failed} failed, {cancelled} cancelled in {total_time:.2f}s")
        
        # Store batch execution record
        await self._store_batch_result(batch_result)
        
        return batch_result
    
    async def _execute_sequential(
        self,
        query_ids: List[UUID],
        endpoint_id: UUID,
        variables_map: Dict[UUID, Dict[str, Any]],
        config: ExecutionConfig
    ) -> List[ExecutionResult]:
        """Execute queries sequentially."""
        results = []
        
        for query_id in query_ids:
            variables = variables_map.get(query_id)
            result = await self.execute_query(query_id, endpoint_id, variables, config)
            results.append(result)
            
            # Short delay between executions to prevent overwhelming
            if len(results) < len(query_ids):
                await asyncio.sleep(0.1)
        
        return results
    
    async def _execute_parallel(
        self,
        query_ids: List[UUID],
        endpoint_id: UUID,
        variables_map: Dict[UUID, Dict[str, Any]],
        config: ExecutionConfig
    ) -> List[ExecutionResult]:
        """Execute queries in parallel with concurrency control."""
        # Create tasks for all queries
        tasks = []
        for query_id in query_ids:
            variables = variables_map.get(query_id)
            task = asyncio.create_task(
                self.execute_query(query_id, endpoint_id, variables, config)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ExecutionResult(
                    execution_id=uuid4(),
                    query_id=query_ids[i],
                    endpoint_id=endpoint_id,
                    status=ExecutionStatus.FAILED,
                    started_at=datetime.now(timezone.utc),
                    error_message=str(result),
                    error_code="TASK_EXCEPTION",
                    variables=variables_map.get(query_ids[i])
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def _execute_by_priority(
        self,
        query_ids: List[UUID],
        endpoint_id: UUID,
        variables_map: Dict[UUID, Dict[str, Any]],
        config: ExecutionConfig
    ) -> List[ExecutionResult]:
        """Execute queries ordered by priority."""
        # Get queries and sort by priority
        queries = []
        for query_id in query_ids:
            query = await self.collection_manager.get_query(query_id)
            if query:
                queries.append(query)
        
        # Sort by priority (highest first)
        priority_weights = config.priority_weights
        queries.sort(key=lambda q: priority_weights.get(q.priority, 0), reverse=True)
        
        # Execute in priority order
        sorted_ids = [q.id for q in queries]
        return await self._execute_sequential(sorted_ids, endpoint_id, variables_map, config)
    
    async def _execute_adaptive(
        self,
        query_ids: List[UUID],
        endpoint_id: UUID,
        variables_map: Dict[UUID, Dict[str, Any]],
        config: ExecutionConfig
    ) -> List[ExecutionResult]:
        """Execute queries with adaptive strategy based on complexity and system load."""
        # Get queries with complexity scores
        query_complexities = []
        for query_id in query_ids:
            query = await self.collection_manager.get_query(query_id)
            if query:
                complexity = query.expected_complexity_score or 0.0
                query_complexities.append((query_id, complexity))
        
        # Sort by complexity (simple queries first)
        query_complexities.sort(key=lambda x: x[1])
        
        # Group into simple and complex queries
        simple_threshold = 10.0  # Configurable threshold
        simple_queries = [qid for qid, complexity in query_complexities if complexity <= simple_threshold]
        complex_queries = [qid for qid, complexity in query_complexities if complexity > simple_threshold]
        
        results = []
        
        # Execute simple queries in parallel
        if simple_queries:
            logger.info(f"Executing {len(simple_queries)} simple queries in parallel")
            simple_results = await self._execute_parallel(simple_queries, endpoint_id, variables_map, config)
            results.extend(simple_results)
        
        # Execute complex queries sequentially to avoid resource contention
        if complex_queries:
            logger.info(f"Executing {len(complex_queries)} complex queries sequentially")
            complex_results = await self._execute_sequential(complex_queries, endpoint_id, variables_map, config)
            results.extend(complex_results)
        
        return results
    
    # Scheduled Execution
    
    async def schedule_query(
        self,
        query_id: UUID,
        endpoint_id: UUID,
        cron_expression: str,
        config_override: Optional[ExecutionConfig] = None
    ) -> ScheduledExecution:
        """
        Schedule a query for recurring execution using cron expression.
        
        Args:
            query_id: Query to schedule
            endpoint_id: Target endpoint
            cron_expression: Cron expression for scheduling
            config_override: Execution configuration override
            
        Returns:
            ScheduledExecution instance
        """
        # Validate cron expression
        try:
            cron = croniter(cron_expression, datetime.now(timezone.utc))
            next_run = cron.get_next(datetime)
            # Ensure timezone-aware datetime
            if next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        # Create scheduled execution
        scheduled = ScheduledExecution(
            id=uuid4(),
            query_id=query_id,
            cron_expression=cron_expression,
            endpoint_id=endpoint_id,
            config=config_override or self.config,
            next_execution=next_run
        )
        
        self._scheduled_executions[scheduled.id] = scheduled
        
        # Start scheduler if not already running
        if not self._scheduler_task or self._scheduler_task.done():
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"Scheduled query {query_id} with expression '{cron_expression}', next run: {next_run}")
        
        # Store in database
        await self._store_scheduled_execution(scheduled)
        
        return scheduled
    
    async def unschedule_query(self, scheduled_id: UUID) -> bool:
        """Remove a scheduled query execution."""
        if scheduled_id in self._scheduled_executions:
            del self._scheduled_executions[scheduled_id]
            
            # Remove from database
            await self.db_session.execute(
                "DELETE FROM scheduled_executions WHERE id = $1",
                [scheduled_id]
            )
            await self.db_session.commit()
            
            logger.info(f"Unscheduled execution {scheduled_id}")
            return True
        
        return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop for executing scheduled queries."""
        logger.info("Starting query scheduler")
        
        while not self._shutdown_event.is_set():
            try:
                now = datetime.now(timezone.utc)
                
                # Check for due executions
                for scheduled in list(self._scheduled_executions.values()):
                    if scheduled.enabled and scheduled.next_execution and now >= scheduled.next_execution:
                        # Execute query
                        logger.info(f"Executing scheduled query {scheduled.query_id}")
                        
                        # Don't await to avoid blocking scheduler
                        asyncio.create_task(self._execute_scheduled_query(scheduled))
                        
                        # Calculate next execution time
                        cron = croniter(scheduled.cron_expression, now)
                        next_run = cron.get_next(datetime)
                        # Ensure timezone-aware datetime
                        if next_run.tzinfo is None:
                            next_run = next_run.replace(tzinfo=timezone.utc)
                        scheduled.next_execution = next_run
                        scheduled.last_execution = now
                
                # Sleep until next check (every 30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.exception("Error in scheduler loop")
                await asyncio.sleep(60)  # Longer sleep on error
    
    async def _execute_scheduled_query(self, scheduled: ScheduledExecution):
        """Execute a scheduled query."""
        try:
            result = await self.execute_query(
                scheduled.query_id,
                scheduled.endpoint_id,
                config_override=scheduled.config
            )
            
            logger.info(f"Scheduled execution completed: {result.status.value}")
            
        except Exception as e:
            logger.exception(f"Error executing scheduled query {scheduled.query_id}")
    
    # Result Storage and Retrieval
    
    async def _store_execution_result(self, result: ExecutionResult):
        """Store execution result in database."""
        execution = Execution(
            pk_execution=result.execution_id,
            fk_query=result.query_id,
            fk_endpoint=result.endpoint_id,  # Assuming this exists in ExecutionResult
            execution_start=result.started_at,
            execution_end=result.completed_at,
            status=result.status.value,
            response_time_ms=int(result.execution_time * 1000) if result.execution_time else None,
            response_size_bytes=result.response_size,
            actual_complexity_score=result.complexity_score,
            error_message=result.error_message,
            error_code=result.error_code,
            response_data=result.result_data,
            variables_used=result.variables or {},
            execution_context={"cache_hit": result.cache_hit} if hasattr(result, 'cache_hit') else {}
        )
        
        self.db_session.add(execution)
        await self.db_session.commit()
    
    async def _store_batch_result(self, batch_result: BatchExecutionResult):
        """Store batch execution result."""
        # Store individual results (already done in _store_execution_result)
        
        # Store batch summary
        await self.db_session.execute("""
            INSERT INTO batch_executions (
                id, total_queries, successful, failed, cancelled, 
                total_time, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, [
            batch_result.batch_id,
            batch_result.total_queries,
            batch_result.successful,
            batch_result.failed,
            batch_result.cancelled,
            batch_result.total_time,
            datetime.now(timezone.utc)
        ])
        
        await self.db_session.commit()
    
    async def _store_scheduled_execution(self, scheduled: ScheduledExecution):
        """Store scheduled execution configuration."""
        await self.db_session.execute("""
            INSERT INTO scheduled_executions (
                id, query_id, cron_expression, endpoint_id, config,
                enabled, created_at, next_execution
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, [
            scheduled.id,
            scheduled.query_id,
            scheduled.cron_expression,
            scheduled.endpoint_id,
            json.dumps(self._serialize_config(scheduled.config)),
            scheduled.enabled,
            scheduled.created_at,
            scheduled.next_execution
        ])
        
        await self.db_session.commit()
    
    def _serialize_config(self, config: ExecutionConfig) -> dict:
        """Serialize ExecutionConfig to JSON-compatible dictionary."""
        result = config.__dict__.copy()
        # Convert enum keys to strings
        if 'priority_weights' in result:
            result['priority_weights'] = {
                str(k): v for k, v in result['priority_weights'].items()
            }
        return result
    
    # Metrics and Monitoring
    
    def _update_execution_metrics(self, result: ExecutionResult):
        """Update internal execution metrics."""
        self._execution_metrics["total_executions"] += 1
        
        if result.success:
            self._execution_metrics["successful_executions"] += 1
        else:
            self._execution_metrics["failed_executions"] += 1
        
        if result.execution_time:
            total_time = self._execution_metrics["total_execution_time"]
            total_executions = self._execution_metrics["total_executions"]
            
            total_time += result.execution_time
            self._execution_metrics["total_execution_time"] = total_time
            self._execution_metrics["avg_execution_time"] = total_time / total_executions
    
    async def get_execution_metrics(self) -> Dict[str, Any]:
        """Get comprehensive execution metrics."""
        # Get database metrics
        db_metrics = await self.db_session.execute("""
            SELECT 
                COUNT(*) as total_db_executions,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_db,
                AVG(execution_time) as avg_time_db,
                COUNT(DISTINCT query_id) as unique_queries,
                MAX(started_at) as last_execution
            FROM query_executions
            WHERE started_at >= NOW() - INTERVAL '24 hours'
        """)
        
        db_stats = db_metrics[0] if db_metrics else {}
        
        return {
            **self._execution_metrics,
            "db_metrics": db_stats,
            "active_executions": len(self._running_executions),
            "scheduled_executions": len(self._scheduled_executions),
            "scheduler_running": self._scheduler_task and not self._scheduler_task.done()
        }
    
    async def get_query_execution_history(
        self,
        query_id: UUID,
        limit: int = 100
    ) -> List[Execution]:
        """Get execution history for a specific query."""
        results = await self.db_session.execute("""
            SELECT * FROM query_executions 
            WHERE query_id = $1 
            ORDER BY started_at DESC 
            LIMIT $2
        """, [query_id, limit])
        
        return [Execution.from_dict(row) for row in results]
    
    # Lifecycle Management
    
    async def start(self):
        """Start the execution manager and scheduler."""
        # Load scheduled executions from database
        scheduled_results = await self.db_session.execute("""
            SELECT * FROM scheduled_executions WHERE enabled = true
        """)
        
        for row in scheduled_results:
            scheduled = ScheduledExecution(
                id=row["id"],
                query_id=row["query_id"],
                cron_expression=row["cron_expression"],
                endpoint_id=row["endpoint_id"],
                config=ExecutionConfig(**json.loads(row["config"])),
                enabled=row["enabled"],
                created_at=row["created_at"],
                last_execution=row["last_execution"],
                next_execution=row["next_execution"]
            )
            self._scheduled_executions[scheduled.id] = scheduled
        
        # Start scheduler
        if self._scheduled_executions and not self._scheduler_task:
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info(f"Execution manager started with {len(self._scheduled_executions)} scheduled executions")
    
    async def stop(self):
        """Stop the execution manager and clean up resources."""
        logger.info("Stopping execution manager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel scheduler
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Cancel running executions
        for task in self._running_executions.values():
            task.cancel()
        
        if self._running_executions:
            await asyncio.gather(*self._running_executions.values(), return_exceptions=True)
        
        # Cleanup thread pool
        self._thread_pool.shutdown(wait=True)
        
        logger.info("Execution manager stopped")