"""Main API router for v1."""

from fastapi import APIRouter

from .endpoints import endpoints_router
from .queries import queries_router
from .executions_simple import executions_router
from .websocket import websocket_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(endpoints_router, prefix="/endpoints", tags=["Endpoints"])
api_router.include_router(queries_router, prefix="/queries", tags=["Queries"])
api_router.include_router(executions_router, prefix="/executions", tags=["Query History"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])