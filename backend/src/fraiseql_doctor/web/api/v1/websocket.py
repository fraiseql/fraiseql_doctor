"""WebSocket endpoints for real-time updates."""

import json
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from starlette.applications import Starlette

from ...core.websocket_manager import WebSocketManager

websocket_router = APIRouter()


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager from app state."""
    # This will be injected by FastAPI app
    # For now, create a singleton
    if not hasattr(get_websocket_manager, '_manager'):
        get_websocket_manager._manager = WebSocketManager()
    return get_websocket_manager._manager


@websocket_router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates."""
    manager = get_websocket_manager()
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get('type')
            
            if message_type == 'subscribe_endpoint':
                endpoint_id = message.get('endpoint_id')
                if endpoint_id:
                    await manager.subscribe_to_endpoint(websocket, endpoint_id)
                    await manager.send_personal_message({
                        'type': 'subscription_confirmed',
                        'endpoint_id': endpoint_id
                    }, websocket)
            
            elif message_type == 'unsubscribe_endpoint':
                endpoint_id = message.get('endpoint_id')
                if endpoint_id:
                    await manager.unsubscribe_from_endpoint(websocket, endpoint_id)
                    await manager.send_personal_message({
                        'type': 'unsubscription_confirmed',
                        'endpoint_id': endpoint_id
                    }, websocket)
            
            elif message_type == 'ping':
                await manager.send_personal_message({
                    'type': 'pong'
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)