"""Query-related Pydantic schemas for validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryCreate(BaseModel):
    """Schema for creating a new query."""

    name: str = Field(..., min_length=1, max_length=255, description="Query name")
    description: str | None = Field(None, description="Query description")
    query_text: str = Field(..., min_length=1, description="GraphQL query text")
    variables: dict[str, Any] = Field(default_factory=dict, description="Query variables")
    expected_complexity_score: int | None = Field(
        None, ge=0, description="Expected complexity score"
    )
    tags: list[str] = Field(default_factory=list, description="Query tags")
    created_by: str = Field(..., min_length=1, description="Creator identifier")
    query_metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate query name format."""
        if not v or not v.strip():
            raise ValueError("Query name cannot be empty")
        return v.strip()

    @field_validator("query_text")
    @classmethod
    def validate_query_text(cls, v):
        """Validate GraphQL query text."""
        if not v or not v.strip():
            raise ValueError("Query text cannot be empty")
        # Basic GraphQL validation - should contain 'query' or 'mutation'
        if "query" not in v.lower() and "mutation" not in v.lower():
            raise ValueError("Query text must contain a valid GraphQL operation")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        return [tag.strip() for tag in v if tag.strip()]


class QueryUpdate(BaseModel):
    """Schema for updating an existing query."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    query_text: str | None = Field(None, min_length=1)
    variables: dict[str, Any] | None = None
    expected_complexity_score: int | None = Field(None, ge=0)
    tags: list[str] | None = None
    is_active: bool | None = None
    query_metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate query name format."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Query name cannot be empty")
        return v.strip() if v else None

    @field_validator("query_text")
    @classmethod
    def validate_query_text(cls, v):
        """Validate GraphQL query text."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Query text cannot be empty")
            if "query" not in v.lower() and "mutation" not in v.lower():
                raise ValueError("Query text must contain a valid GraphQL operation")
            return v.strip()
        return v


class QueryCollectionCreate(BaseModel):
    """Schema for creating a new query collection."""

    name: str = Field(..., min_length=1, max_length=255, description="Collection name")
    description: str | None = Field(None, description="Collection description")
    tags: list[str] = Field(default_factory=list, description="Collection tags")
    created_by: str = Field(..., min_length=1, description="Creator identifier")
    is_active: bool = Field(default=True, description="Whether the collection is active")
    initial_queries: list[QueryCreate] = Field(
        default_factory=list, description="Initial queries to add"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate collection name format."""
        if not v or not v.strip():
            raise ValueError("Collection name cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags are non-empty strings."""
        return [tag.strip() for tag in v if tag.strip()]


class QueryCollectionUpdate(BaseModel):
    """Schema for updating an existing query collection."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate collection name format."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Collection name cannot be empty")
        return v.strip() if v else None


class QueryResponse(BaseModel):
    """Schema for query response data."""

    pk_query: UUID
    name: str
    description: str | None
    query_text: str
    variables: dict[str, Any]
    expected_complexity_score: int | None
    tags: list[str]
    is_active: bool
    created_by: str | None
    query_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
