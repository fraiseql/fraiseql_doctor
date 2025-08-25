"""Queries management API."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraiseql_doctor.models.query import Query

from ...core.database import get_database_session

queries_router = APIRouter()


@queries_router.get("/")
async def get_queries(db: AsyncSession = Depends(get_database_session)) -> list[dict]:
    """Get all queries."""
    query = select(Query).where(Query.is_active == True)
    result = await db.execute(query)
    queries = result.scalars().all()

    return [
        {
            "id": str(query.pk_query),
            "name": query.name,
            "description": query.description,
            "query": query.query_text,
            "variables": query.variables,
            "tags": query.tags,
        }
        for query in queries
    ]
