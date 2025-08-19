"""Endpoint-related Pydantic schemas for validation."""
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict, HttpUrl


class EndpointCreate(BaseModel):
    """Schema for creating a new endpoint."""
    name: str = Field(..., min_length=1, max_length=255, description="Endpoint name")
    url: str = Field(..., description="GraphQL endpoint URL")
    auth_type: str = Field(..., description="Authentication type")
    auth_config: dict[str, Any] = Field(default_factory=dict, description="Authentication configuration")
    headers: dict[str, Any] = Field(default_factory=dict, description="Additional headers")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=1, ge=0, le=60, description="Delay between retries")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate endpoint name format."""
        if not v or not v.strip():
            raise ValueError('Endpoint name cannot be empty')
        return v.strip()

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError('URL cannot be empty')
        
        # Basic URL validation
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        
        return v

    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v):
        """Validate authentication type."""
        allowed_types = ['none', 'bearer', 'basic', 'api_key', 'oauth2']
        if v not in allowed_types:
            raise ValueError(f'Auth type must be one of: {", ".join(allowed_types)}')
        return v


class EndpointUpdate(BaseModel):
    """Schema for updating an existing endpoint."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict[str, Any]] = None
    headers: Optional[dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0, le=60)
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate endpoint name format."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Endpoint name cannot be empty')
        return v.strip() if v else None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('URL cannot be empty')
            
            v = v.strip()
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError('URL must start with http:// or https://')
            
            return v
        return v

    @field_validator('auth_type')
    @classmethod
    def validate_auth_type(cls, v):
        """Validate authentication type."""
        if v is not None:
            allowed_types = ['none', 'bearer', 'basic', 'api_key', 'oauth2']
            if v not in allowed_types:
                raise ValueError(f'Auth type must be one of: {", ".join(allowed_types)}')
        return v


class EndpointResponse(BaseModel):
    """Schema for endpoint response data."""
    pk_endpoint: UUID
    name: str
    url: str
    auth_type: str
    auth_config: dict[str, Any]
    headers: dict[str, Any]
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    is_active: bool
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)