"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.database import get_database_session
from .core.websocket_manager import WebSocketManager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting FraiseQL Doctor API...")
    
    # Initialize WebSocket manager
    app.state.websocket_manager = WebSocketManager()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down FraiseQL Doctor API...")


# Create FastAPI application
app = FastAPI(
    title="FraiseQL Doctor API",
    description="Backend API for FraiseQL Doctor - GraphQL endpoint monitoring and query management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint - API health check."""
    return {
        "message": "FraiseQL Doctor API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


def main() -> None:
    """Main entry point for running the API server."""
    import uvicorn
    
    uvicorn.run(
        "fraiseql_doctor.web.main:app",
        host="0.0.0.0",
        port=8001,  # Use different port to avoid conflicts
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()