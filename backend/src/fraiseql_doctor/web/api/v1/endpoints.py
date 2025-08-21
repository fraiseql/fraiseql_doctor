"""Endpoints management API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraiseql_doctor.models.endpoint import Endpoint

from ...core.database import get_database_session

endpoints_router = APIRouter()


@endpoints_router.get("/")
async def get_endpoints(db: AsyncSession = Depends(get_database_session)) -> list[dict]:
    """Get all endpoints."""
    query = select(Endpoint).where(Endpoint.is_active == True)
    result = await db.execute(query)
    endpoints = result.scalars().all()

    return [
        {
            "id": str(endpoint.pk_endpoint),
            "name": endpoint.name,
            "url": endpoint.url,
            "auth_type": endpoint.auth_type,
            "is_healthy": True,  # TODO: Implement actual health check
            "status": "active",
        }
        for endpoint in endpoints
    ]


@endpoints_router.get("/{endpoint_id}")
async def get_endpoint(endpoint_id: UUID, db: AsyncSession = Depends(get_database_session)) -> dict:
    """Get endpoint by ID."""
    query = select(Endpoint).where(Endpoint.pk_endpoint == endpoint_id)
    result = await db.execute(query)
    endpoint = result.scalar_one_or_none()

    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return {
        "id": str(endpoint.pk_endpoint),
        "name": endpoint.name,
        "url": endpoint.url,
        "auth_type": endpoint.auth_type,
        "headers": endpoint.headers,
        "introspectionEnabled": True,  # TODO: Add to model
        "is_healthy": True,
        "status": "active",
        "createdAt": endpoint.created_at.isoformat() if endpoint.created_at else None,
        "updatedAt": endpoint.updated_at.isoformat() if endpoint.updated_at else None,
    }
