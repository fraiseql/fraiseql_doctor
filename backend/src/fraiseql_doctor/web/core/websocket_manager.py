"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Dict, List, Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_subscriptions: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = {}
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            self.disconnect(websocket)
    
    async def broadcast_message(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected_clients = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected_clients.append(connection)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            self.disconnect(client)
    
    async def subscribe_to_endpoint(self, websocket: WebSocket, endpoint_id: str) -> None:
        """Subscribe a client to endpoint updates."""
        if websocket in self.client_subscriptions:
            if 'endpoints' not in self.client_subscriptions[websocket]:
                self.client_subscriptions[websocket]['endpoints'] = []
            
            if endpoint_id not in self.client_subscriptions[websocket]['endpoints']:
                self.client_subscriptions[websocket]['endpoints'].append(endpoint_id)
                logger.info(f"Client subscribed to endpoint {endpoint_id}")
    
    async def unsubscribe_from_endpoint(self, websocket: WebSocket, endpoint_id: str) -> None:
        """Unsubscribe a client from endpoint updates."""
        if websocket in self.client_subscriptions:
            endpoints = self.client_subscriptions[websocket].get('endpoints', [])
            if endpoint_id in endpoints:
                endpoints.remove(endpoint_id)
                logger.info(f"Client unsubscribed from endpoint {endpoint_id}")
    
    async def notify_query_execution(self, endpoint_id: str, execution_data: dict) -> None:
        """Notify subscribed clients about query execution."""
        message = {
            "type": "query_execution",
            "endpoint_id": endpoint_id,
            "data": execution_data
        }
        
        # Send to subscribed clients
        for websocket, subscriptions in self.client_subscriptions.items():
            endpoints = subscriptions.get('endpoints', [])
            if endpoint_id in endpoints:
                await self.send_personal_message(message, websocket)
    
    async def notify_health_update(self, endpoint_id: str, health_data: dict) -> None:
        """Notify subscribed clients about health status updates."""
        message = {
            "type": "health_update",
            "endpoint_id": endpoint_id,
            "data": health_data
        }
        
        # Send to subscribed clients
        for websocket, subscriptions in self.client_subscriptions.items():
            endpoints = subscriptions.get('endpoints', [])
            if endpoint_id in endpoints:
                await self.send_personal_message(message, websocket)