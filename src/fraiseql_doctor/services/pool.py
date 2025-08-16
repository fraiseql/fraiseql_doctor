"""Connection pool management for multiple endpoints."""
import asyncio
from typing import Dict, Optional
from uuid import UUID

import aiohttp

from fraiseql_doctor.models.endpoint import Endpoint


class ConnectionPoolManager:
    """Manage connection pools for multiple FraiseQL endpoints."""
    
    def __init__(self, max_connections_per_endpoint: int = 10):
        self._pools: Dict[UUID, aiohttp.ClientSession] = {}
        self._max_connections = max_connections_per_endpoint
        self._lock = asyncio.Lock()
    
    async def get_session(self, endpoint: Endpoint) -> aiohttp.ClientSession:
        """Get or create a session for the endpoint."""
        async with self._lock:
            if endpoint.id not in self._pools:
                connector = aiohttp.TCPConnector(
                    limit=self._max_connections,
                    limit_per_host=self._max_connections,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True,
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=endpoint.timeout_seconds or 30,
                    connect=10,
                    sock_read=endpoint.timeout_seconds or 30,
                    sock_connect=10
                )
                
                # Base headers for the session
                session_headers = {
                    "User-Agent": "FraiseQL-Doctor/1.0",
                    "Accept": "application/json",
                }
                
                # Add endpoint-specific headers
                if endpoint.headers:
                    session_headers.update(endpoint.headers)
                
                self._pools[endpoint.id] = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=session_headers,
                    raise_for_status=False  # We handle HTTP errors manually
                )
            
            return self._pools[endpoint.id]
    
    async def close_session(self, endpoint_id: UUID) -> None:
        """Close session for specific endpoint."""
        async with self._lock:
            if endpoint_id in self._pools:
                session = self._pools[endpoint_id]
                if not session.closed:
                    await session.close()
                del self._pools[endpoint_id]
    
    async def close_all(self) -> None:
        """Close all sessions."""
        async with self._lock:
            for session in self._pools.values():
                if not session.closed:
                    await session.close()
            self._pools.clear()
    
    async def get_pool_stats(self) -> Dict[str, any]:
        """Get statistics about connection pools."""
        async with self._lock:
            stats = {
                "total_pools": len(self._pools),
                "pools": []
            }
            
            for endpoint_id, session in self._pools.items():
                connector = session.connector
                if isinstance(connector, aiohttp.TCPConnector):
                    pool_stats = {
                        "endpoint_id": str(endpoint_id),
                        "closed": session.closed,
                        "connector_limit": connector.limit,
                        "connector_limit_per_host": connector.limit_per_host,
                    }
                    stats["pools"].append(pool_stats)
            
            return stats
    
    async def health_check_all(self) -> Dict[UUID, Dict[str, any]]:
        """Perform health check on all active sessions."""
        async with self._lock:
            results = {}
            
            for endpoint_id, session in self._pools.items():
                results[endpoint_id] = {
                    "session_closed": session.closed,
                    "connector_closed": getattr(session.connector, "closed", True),
                }
            
            return results
    
    def __len__(self) -> int:
        """Return number of active pools."""
        return len(self._pools)
    
    def __contains__(self, endpoint_id: UUID) -> bool:
        """Check if endpoint has an active pool."""
        return endpoint_id in self._pools