"""Query Collection Management System

Provides comprehensive management of GraphQL queries including:
- CRUD operations for query organization
- Collection-based grouping and categorization
- Query validation and metadata tracking
- Search and filtering capabilities
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ..models.query import Query
from ..models.query_collection import QueryCollection
from ..schemas.query import QueryCollectionCreate, QueryCollectionUpdate, QueryCreate, QueryUpdate
from ..services.complexity import QueryComplexityAnalyzer


class QueryStatus(Enum):
    """Query execution status states."""

    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ERROR = "error"


class QueryPriority(Enum):
    """Query execution priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueryCollectionMetrics:
    """Metrics for query collection performance tracking."""

    total_queries: int = 0
    active_queries: int = 0
    avg_complexity_score: float = 0.0
    total_executions: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    last_executed: datetime | None = None


@dataclass
class QuerySearchFilter:
    """Advanced search and filtering options for queries."""

    text: str | None = None
    status: QueryStatus | None = None
    priority: QueryPriority | None = None
    collection_ids: list[UUID] | None = None
    complexity_min: float | None = None
    complexity_max: float | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    tags: set[str] | None = None
    limit: int = 100
    offset: int = 0


class QueryCollectionManager:
    """Manages GraphQL query collections with advanced organization and search capabilities.

    Provides:
    - Collection CRUD operations
    - Query organization and categorization
    - Advanced search and filtering
    - Query validation and complexity analysis
    - Performance metrics tracking
    """

    def __init__(self, db_session, complexity_analyzer: QueryComplexityAnalyzer):
        self.db_session = db_session
        self.complexity_analyzer = complexity_analyzer
        self._cache: dict[UUID, QueryCollection] = {}
        self._query_cache: dict[UUID, Query] = {}

    # Collection Management

    async def create_collection(
        self, schema: QueryCollectionCreate, validate_queries: bool = True
    ) -> QueryCollection:
        """Create a new query collection with optional query validation.

        Args:
        ----
            schema: Collection creation schema
            validate_queries: Whether to validate GraphQL syntax

        Returns:
        -------
            Created QueryCollection instance

        Raises:
        ------
            ValueError: If collection name already exists or validation fails

        """
        # Check for duplicate names
        existing = await self.get_collection_by_name(schema.name)
        if existing:
            raise ValueError(f"Collection with name '{schema.name}' already exists")

        # Create collection
        collection = QueryCollection(
            pk_query_collection=uuid4(),
            name=schema.name,
            description=schema.description,
            tags=dict.fromkeys(schema.tags, True) if schema.tags else {},
            is_active=schema.is_active,
            created_by=schema.created_by,
            collection_metadata=schema.metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Add initial queries if provided
        if schema.initial_queries:
            for query_data in schema.initial_queries:
                await self._add_query_to_collection(
                    collection, query_data, validate=validate_queries
                )

        # Store in database
        self.db_session.add(collection)
        await self.db_session.commit()

        # Cache and return
        self._cache[collection.pk_query_collection] = collection
        return collection

    async def get_collection(self, collection_id: UUID) -> QueryCollection | None:
        """Get collection by ID with caching."""
        if collection_id in self._cache:
            return self._cache[collection_id]

        collection = await self.db_session.get(QueryCollection, collection_id)
        if collection:
            self._cache[collection_id] = collection

        return collection

    async def get_collection_by_name(self, name: str) -> QueryCollection | None:
        """Get collection by name."""
        result = await self.db_session.execute(
            "SELECT * FROM query_collections WHERE name = $1", [name]
        )

        if result:
            collection = QueryCollection.from_dict(result[0])
            self._cache[collection.pk_query_collection] = collection
            return collection

        return None

    async def update_collection(
        self, collection_id: UUID, schema: QueryCollectionUpdate
    ) -> QueryCollection | None:
        """Update existing collection."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return None

        # Update fields
        if schema.name is not None:
            # Check for name conflicts
            existing = await self.get_collection_by_name(schema.name)
            if existing and existing.id != collection_id:
                raise ValueError(f"Collection with name '{schema.name}' already exists")
            collection.name = schema.name

        if schema.description is not None:
            collection.description = schema.description

        if schema.tags is not None:
            collection.tags = set(schema.tags)

        if schema.is_active is not None:
            collection.is_active = schema.is_active

        collection.updated_at = datetime.now(UTC)

        # Update database
        await self.db_session.commit()

        # Update cache
        self._cache[collection_id] = collection
        return collection

    async def delete_collection(self, collection_id: UUID, force: bool = False) -> bool:
        """Delete collection and optionally its queries.

        Args:
        ----
            collection_id: Collection to delete
            force: If True, delete even if it has queries

        Returns:
        -------
            True if deleted successfully

        """
        collection = await self.get_collection(collection_id)
        if not collection:
            return False

        # Check for queries if not forcing
        if not force and collection.queries:
            raise ValueError(
                f"Collection has {len(collection.queries)} queries. "
                "Use force=True to delete anyway."
            )

        # Delete from database
        await self.db_session.delete(collection)
        await self.db_session.commit()

        # Remove from cache
        if collection_id in self._cache:
            del self._cache[collection_id]

        return True

    async def list_collections(
        self, active_only: bool = False, include_metrics: bool = False
    ) -> list[QueryCollection]:
        """List all collections with optional filtering and metrics."""
        query = "SELECT * FROM query_collections"
        params = []

        if active_only:
            query += " WHERE is_active = $1"
            params.append(True)

        query += " ORDER BY name"

        results = await self.db_session.execute(query, params)
        collections = [QueryCollection.from_dict(row) for row in results]

        # Add metrics if requested
        if include_metrics:
            for collection in collections:
                collection.metrics = await self._calculate_collection_metrics(
                    collection.pk_query_collection
                )

        return collections

    # Query Management

    async def add_query(
        self, collection_id: UUID, schema: QueryCreate, validate: bool = True
    ) -> Query | None:
        """Add a new query to a collection."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return None

        return await self._add_query_to_collection(collection, schema, validate)

    async def _add_query_to_collection(
        self, collection: QueryCollection, schema: QueryCreate, validate: bool = True
    ) -> Query:
        """Internal method to add query to collection."""
        # Validate GraphQL syntax if requested
        if validate:
            try:
                analysis = await self.complexity_analyzer.analyze_query(schema.query_text)
            except Exception as e:
                raise ValueError(f"Invalid GraphQL query: {e}")
        else:
            analysis = None

        # Create query
        query = Query(
            pk_query=uuid4(),
            name=schema.name,
            description=schema.description,
            query_text=schema.query_text,
            variables=schema.variables or {},
            expected_complexity_score=int(analysis.complexity_score) if analysis else 0,
            tags=schema.tags or [],
            is_active=True,
            created_by=schema.created_by,
            query_metadata={
                "collection_id": str(collection.pk_query_collection),
                "complexity_score": analysis.complexity_score if analysis else 0.0,
                "estimated_cost": analysis.estimated_execution_time if analysis else 0.0,
                "field_count": analysis.field_count if analysis else 0,
                "depth": analysis.depth if analysis else 0,
                "last_validated": datetime.now(UTC).isoformat() if validate else None,
            },
        )

        # Note: In this simplified version, we just create the query
        # In a full implementation, queries would be stored separately
        # and linked to collections via collection_id in metadata

        collection.updated_at = datetime.now(UTC)

        # Store in database
        self.db_session.add(query)
        await self.db_session.commit()

        # Cache query
        self._query_cache[query.pk_query] = query

        return query

    async def get_query(self, query_id: UUID) -> Query | None:
        """Get query by ID with caching."""
        if query_id in self._query_cache:
            return self._query_cache[query_id]

        query = await self.db_session.get(Query, query_id)
        if query:
            self._query_cache[query_id] = query

        return query

    async def update_query(
        self, query_id: UUID, schema: QueryUpdate, validate: bool = True
    ) -> Query | None:
        """Update existing query with optional validation."""
        query = await self.get_query(query_id)
        if not query:
            return None

        # Update content and re-analyze if changed
        if schema.query_text is not None and schema.query_text != query.query_text:
            if validate:
                try:
                    analysis = await self.complexity_analyzer.analyze_query(schema.query_text)
                    query.metadata.complexity_score = analysis.complexity_score
                    query.metadata.estimated_cost = analysis.estimated_execution_time
                    query.metadata.field_count = analysis.field_count
                    query.metadata.depth = analysis.depth
                    query.metadata.last_validated = datetime.now(UTC)
                except Exception as e:
                    raise ValueError(f"Invalid GraphQL query: {e}")

            query.query_text = schema.query_text

        # Update other fields
        if schema.name is not None:
            query.name = schema.name

        if schema.description is not None:
            query.description = schema.description

        if schema.variables is not None:
            query.variables = schema.variables

        if getattr(schema, "status", None) is not None:
            query.status = QueryStatus(schema.status)

        if getattr(schema, "priority", None) is not None:
            query.priority = QueryPriority(schema.priority)

        if schema.tags is not None:
            query.tags = set(schema.tags)

        query.updated_at = datetime.now(UTC)

        # Update database
        await self.db_session.commit()

        # Update cache
        self._query_cache[query_id] = query
        return query

    async def delete_query(self, query_id: UUID) -> bool:
        """Delete a query."""
        query = await self.get_query(query_id)
        if not query:
            return False

        # Remove from collection
        collection = await self.get_collection(query.collection_id)
        if collection:
            collection.queries = [q for q in collection.queries if q.id != query_id]
            collection.updated_at = datetime.now(UTC)

        # Delete from database
        await self.db_session.delete(query)
        await self.db_session.commit()

        # Remove from cache
        if query_id in self._query_cache:
            del self._query_cache[query_id]

        return True

    # Search and Filtering

    async def search_queries(self, filter_params: QuerySearchFilter) -> list[Query]:
        """Advanced query search with multiple filter criteria."""
        query_parts = ["SELECT * FROM queries WHERE 1=1"]
        params = []
        param_counter = 0

        # Text search in name, description, or content
        if filter_params.text:
            param_counter += 1
            query_parts.append(
                f"""
                AND (
                    name ILIKE ${param_counter} OR
                    description ILIKE ${param_counter} OR
                    content ILIKE ${param_counter}
                )
            """
            )
            params.append(f"%{filter_params.text}%")

        # Status filter
        if filter_params.status:
            param_counter += 1
            query_parts.append(f"AND status = ${param_counter}")
            params.append(filter_params.status.value)

        # Priority filter
        if filter_params.priority:
            param_counter += 1
            query_parts.append(f"AND priority = ${param_counter}")
            params.append(filter_params.priority.value)

        # Collection filter
        if filter_params.collection_ids:
            param_counter += 1
            query_parts.append(f"AND collection_id = ANY(${param_counter})")
            params.append(filter_params.collection_ids)

        # Complexity range
        if filter_params.complexity_min is not None:
            param_counter += 1
            query_parts.append(f"AND metadata->>'complexity_score' >= ${param_counter}")
            params.append(str(filter_params.complexity_min))

        if filter_params.complexity_max is not None:
            param_counter += 1
            query_parts.append(f"AND metadata->>'complexity_score' <= ${param_counter}")
            params.append(str(filter_params.complexity_max))

        # Date range
        if filter_params.created_after:
            param_counter += 1
            query_parts.append(f"AND created_at >= ${param_counter}")
            params.append(filter_params.created_after)

        if filter_params.created_before:
            param_counter += 1
            query_parts.append(f"AND created_at <= ${param_counter}")
            params.append(filter_params.created_before)

        # Tags filter (PostgreSQL array contains)
        if filter_params.tags:
            param_counter += 1
            query_parts.append(f"AND tags @> ${param_counter}")
            params.append(list(filter_params.tags))

        # Pagination
        query_parts.append("ORDER BY created_at DESC")

        param_counter += 1
        query_parts.append(f"LIMIT ${param_counter}")
        params.append(filter_params.limit)

        param_counter += 1
        query_parts.append(f"OFFSET ${param_counter}")
        params.append(filter_params.offset)

        final_query = " ".join(query_parts)
        results = await self.db_session.execute(final_query, params)

        return [Query.from_dict(row) for row in results]

    # Metrics and Analytics

    async def _calculate_collection_metrics(self, collection_id: UUID) -> QueryCollectionMetrics:
        """Calculate performance metrics for a collection."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return QueryCollectionMetrics()

        # Query database for queries in this collection
        query_results = await self.db_session.execute(
            """SELECT * FROM queries WHERE collection_id = $1""", [collection_id]
        )
        queries = query_results if query_results else []

        total_queries = len(queries)
        active_queries = len([q for q in queries if q.get("is_active", True)])

        if total_queries == 0:
            return QueryCollectionMetrics(
                total_queries=0, active_queries=0, avg_complexity_score=0.0
            )

        # Calculate average complexity
        complexity_scores = [
            q.get("complexity_score", 0.0) for q in queries if q.get("complexity_score", 0.0) > 0
        ]
        avg_complexity = (
            sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0
        )

        # Get execution stats from database using the query IDs from our results
        query_ids = [q.get("id") for q in queries if q.get("id")]
        if query_ids:
            exec_stats = await self.db_session.execute(
                """
                SELECT
                    COUNT(*) as total_executions,
                    AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time) as avg_execution_time,
                    MAX(executed_at) as last_executed
                FROM query_executions
                WHERE query_id = ANY($1)
            """,
                [query_ids],
            )
        else:
            exec_stats = []

        if exec_stats and len(exec_stats) > 0:
            stats = exec_stats[0]
            return QueryCollectionMetrics(
                total_queries=total_queries,
                active_queries=active_queries,
                avg_complexity_score=avg_complexity,
                total_executions=stats.get("total_executions", 0) or 0,
                success_rate=float(stats.get("success_rate", 0.0) or 0.0),
                avg_execution_time=float(stats.get("avg_execution_time", 0.0) or 0.0),
                last_executed=stats.get("last_executed"),
            )

        return QueryCollectionMetrics(
            total_queries=total_queries,
            active_queries=active_queries,
            avg_complexity_score=avg_complexity,
        )

    async def get_collection_metrics(self, collection_id: UUID) -> QueryCollectionMetrics | None:
        """Get metrics for a specific collection."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return None

        return await self._calculate_collection_metrics(collection_id)

    # Bulk Operations

    async def bulk_update_query_status(self, query_ids: list[UUID], status: QueryStatus) -> int:
        """Bulk update status for multiple queries."""
        if not query_ids:
            return 0

        result = await self.db_session.execute(
            "UPDATE queries SET status = $1, updated_at = $2 WHERE id = ANY($3)",
            [status.value, datetime.now(UTC), query_ids],
        )

        await self.db_session.commit()

        # Update cache
        for query_id in query_ids:
            if query_id in self._query_cache:
                self._query_cache[query_id].status = status
                self._query_cache[query_id].updated_at = datetime.now(UTC)

        return result.rowcount if hasattr(result, "rowcount") else len(query_ids)

    async def validate_all_queries(self, collection_id: UUID) -> dict[str, Any]:
        """Validate all queries in a collection and return results."""
        collection = await self.get_collection(collection_id)
        if not collection:
            return {"error": "Collection not found"}

        results = {"total": len(collection.queries), "valid": 0, "invalid": 0, "errors": []}

        for query in collection.queries:
            try:
                analysis = await self.complexity_analyzer.analyze_query(query.query_text)
                query.metadata.complexity_score = analysis.complexity_score
                query.metadata.estimated_cost = analysis.estimated_execution_time
                query.metadata.field_count = analysis.field_count
                query.metadata.depth = analysis.depth
                query.metadata.last_validated = datetime.now(UTC)
                query.status = QueryStatus.VALIDATED
                results["valid"] += 1
            except Exception as e:
                query.status = QueryStatus.ERROR
                results["invalid"] += 1
                results["errors"].append(
                    {"query_id": str(query.pk_query), "query_name": query.name, "error": str(e)}
                )

        await self.db_session.commit()
        return results
