"""Query model for storing GraphQL queries."""

import enum
from typing import Any

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    ActiveMixin,
    BaseModel,
    NameDescriptionMixin,
    UserTrackingMixin,
)


class QueryType(enum.Enum):
    """Types of GraphQL operations."""

    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"


class Query(BaseModel, NameDescriptionMixin, ActiveMixin, UserTrackingMixin):
    """GraphQL query storage."""

    __tablename__ = "queries"

    # Query content
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[QueryType] = mapped_column(
        Enum(QueryType), default=QueryType.QUERY, nullable=False
    )
    
    # Variables and metadata
    default_variables: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    expected_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Organization
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Statistics
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[float | None] = mapped_column(nullable=True)
    avg_complexity: Mapped[float | None] = mapped_column(nullable=True)
    
    # Version control
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_query_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Additional metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_use_case: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    executions = relationship("QueryExecution", back_populates="query")
    scheduled_queries = relationship("ScheduledQuery", back_populates="query")

    def __repr__(self) -> str:
        """String representation of the query."""
        return f"<Query(name='{self.name}', type='{self.query_type.value}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 100.0
        return ((self.total_executions - self.total_failures) / self.total_executions) * 100

    def update_stats(self, success: bool, response_time_ms: float, complexity: int | None = None) -> None:
        """Update query statistics."""
        self.total_executions += 1
        if not success:
            self.total_failures += 1

        # Update rolling average response time
        if self.avg_response_time_ms is None:
            self.avg_response_time_ms = response_time_ms
        else:
            # Simple moving average
            weight = 0.1  # Weight for new measurement
            self.avg_response_time_ms = (
                self.avg_response_time_ms * (1 - weight) + response_time_ms * weight
            )

        # Update complexity average if provided
        if complexity is not None:
            if self.avg_complexity is None:
                self.avg_complexity = float(complexity)
            else:
                self.avg_complexity = (
                    self.avg_complexity * (1 - weight) + complexity * weight
                )

    def validate_query_syntax(self) -> list[str]:
        """Validate GraphQL query syntax and return any errors."""
        errors = []
        
        # Basic validation
        if not self.query_text.strip():
            errors.append("Query text cannot be empty")
            return errors
        
        # Check for query type keywords
        query_lower = self.query_text.lower().strip()
        
        if self.query_type == QueryType.QUERY and not query_lower.startswith("query"):
            errors.append("Query type is 'query' but text doesn't start with 'query'")
        elif self.query_type == QueryType.MUTATION and not query_lower.startswith("mutation"):
            errors.append("Query type is 'mutation' but text doesn't start with 'mutation'")
        elif self.query_type == QueryType.SUBSCRIPTION and not query_lower.startswith("subscription"):
            errors.append("Query type is 'subscription' but text doesn't start with 'subscription'")

        # Check for balanced braces
        brace_count = self.query_text.count("{") - self.query_text.count("}")
        if brace_count != 0:
            errors.append(f"Unbalanced braces: {abs(brace_count)} {'opening' if brace_count > 0 else 'closing'} brace(s)")

        return errors

    def extract_variables(self) -> list[str]:
        """Extract variable names from the query."""
        import re
        
        # Find variable declarations in query
        var_pattern = r'\$(\w+)'
        variables = re.findall(var_pattern, self.query_text)
        return list(set(variables))  # Remove duplicates