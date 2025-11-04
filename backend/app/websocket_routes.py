"""
WebSocket Routes for Real-time Communication
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from .websocket_manager import manager
from .security import get_current_user_websocket
from .database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    user = None
    if token:
        try:
            user = await get_current_user_websocket(token, db)
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    
    await manager.connect_chat_session(websocket, session_id)
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "user_id": user.id if user else None,
            "timestamp": "2024-01-01T00:00:00"
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "typing":
                    # Handle typing indicators
                    await manager.send_typing_indicator(
                        session_id, 
                        user.id if user else 0, 
                        message.get("is_typing", False)
                    )
                elif message_type == "message_read":
                    # Handle read receipts
                    await manager.send_message_status(
                        session_id,
                        message.get("message_id"),
                        "read"
                    )
                elif message_type == "ping":
                    # Handle ping/pong for connection health
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00"
                    }))
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received via WebSocket")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect_chat_session(websocket, session_id)
        logger.info(f"WebSocket disconnected from chat session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in chat session {session_id}: {e}")
        manager.disconnect_chat_session(websocket, session_id)

@router.websocket("/ws/habits")
async def websocket_habits_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for habit synchronization"""
    user = None
    if token:
        try:
            user = await get_current_user_websocket(token, db)
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    
    await manager.connect_habit_sync(websocket)
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "habit_sync_connected",
            "user_id": user.id if user else None,
            "timestamp": "2024-01-01T00:00:00"
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "habit_completed":
                    # Broadcast habit completion to other connections
                    await manager.broadcast_habit_update({
                        "type": "habit_update",
                        "action": "completed",
                        "habit_id": message.get("habit_id"),
                        "user_id": user.id if user else None,
                        "timestamp": "2024-01-01T00:00:00"
                    })
                elif message_type == "habit_created":
                    # Broadcast new habit creation
                    await manager.broadcast_habit_update({
                        "type": "habit_update",
                        "action": "created",
                        "habit": message.get("habit"),
                        "user_id": user.id if user else None,
                        "timestamp": "2024-01-01T00:00:00"
                    })
                elif message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00"
                    }))
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON received via WebSocket")
            except Exception as e:
                logger.error(f"Error processing habit WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect_habit_sync(websocket)
        logger.info("WebSocket disconnected from habit synchronization")
    except Exception as e:
        logger.error(f"WebSocket error in habit sync: {e}")
        manager.disconnect_habit_sync(websocket)

@router.websocket("/ws/user/{user_id}")
async def websocket_user_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for user-specific notifications"""
    user = None
    if token:
        try:
            user = await get_current_user_websocket(token, db)
            if user.id != user_id:
                await websocket.close(code=1008, reason="Unauthorized")
                return
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    
    await manager.connect_user(websocket, user_id)
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "user_connected",
            "user_id": user_id,
            "timestamp": "2024-01-01T00:00:00"
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2024-01-01T00:00:00"
                    }))
            except json.JSONDecodeError:
                logger.error("Invalid JSON received via WebSocket")
            except Exception as e:
                logger.error(f"Error processing user WebSocket message: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_id)
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect_user(websocket, user_id)

# Legacy endpoint for backward compatibility
@router.websocket("/api/sync")
async def websocket_sync_endpoint(websocket: WebSocket):
    """Legacy WebSocket endpoint for general synchronization"""
    await manager.connect_habit_sync(websocket)
    
    try:
        await websocket.send_text(json.dumps({
            "type": "sync_connected",
            "timestamp": "2024-01-01T00:00:00"
        }))
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "habit_update":
                    await manager.broadcast_habit_update(message)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.error(f"Error in sync WebSocket: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect_habit_sync(websocket)
    except Exception as e:
        logger.error(f"Sync WebSocket error: {e}")
        manager.disconnect_habit_sync(websocket)