"""
WebSocket Manager for Real-time Communication
Handles WebSocket connections for chat and habit synchronization
"""

import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store session-specific connections for chat
        self.chat_sessions: Dict[str, Set[WebSocket]] = {}
        # Store habit sync connections
        self.habit_connections: Set[WebSocket] = set()
        
    async def connect_user(self, websocket: WebSocket, user_id: int):
        """Connect a user's WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")
        
    async def connect_chat_session(self, websocket: WebSocket, session_id: str):
        """Connect to a specific chat session"""
        await websocket.accept()
        if session_id not in self.chat_sessions:
            self.chat_sessions[session_id] = set()
        self.chat_sessions[session_id].add(websocket)
        logger.info(f"WebSocket connected to chat session {session_id}")
        
    async def connect_habit_sync(self, websocket: WebSocket):
        """Connect for habit synchronization"""
        await websocket.accept()
        self.habit_connections.add(websocket)
        logger.info("WebSocket connected for habit synchronization")
        
    def disconnect_user(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")
        
    def disconnect_chat_session(self, websocket: WebSocket, session_id: str):
        """Disconnect from a chat session"""
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id].discard(websocket)
            if not self.chat_sessions[session_id]:
                del self.chat_sessions[session_id]
        logger.info(f"WebSocket disconnected from chat session {session_id}")
        
    def disconnect_habit_sync(self, websocket: WebSocket):
        """Disconnect from habit synchronization"""
        self.habit_connections.discard(websocket)
        logger.info("WebSocket disconnected from habit synchronization")
        
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to a specific user's connections"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
                
    async def send_chat_message(self, message: dict, session_id: str):
        """Send message to all connections in a chat session"""
        if session_id in self.chat_sessions:
            disconnected = []
            for connection in self.chat_sessions[session_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending chat message to session {session_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.chat_sessions[session_id].discard(conn)
                
    async def broadcast_habit_update(self, message: dict):
        """Broadcast habit updates to all habit sync connections"""
        disconnected = []
        for connection in self.habit_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting habit update: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.habit_connections.discard(conn)
            
    async def send_typing_indicator(self, session_id: str, user_id: int, is_typing: bool):
        """Send typing indicator to chat session"""
        message = {
            "type": "typing_indicator",
            "session_id": session_id,
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_chat_message(message, session_id)
        
    async def send_message_status(self, session_id: str, message_id: str, status: str):
        """Send message delivery status"""
        message = {
            "type": "message_status",
            "session_id": session_id,
            "message_id": message_id,
            "status": status,  # 'sent', 'delivered', 'read'
            "timestamp": datetime.now().isoformat()
        }
        await self.send_chat_message(message, session_id)
        
    def get_active_users(self) -> List[int]:
        """Get list of currently active user IDs"""
        return list(self.active_connections.keys())
        
    def get_session_count(self, session_id: str) -> int:
        """Get number of active connections in a chat session"""
        return len(self.chat_sessions.get(session_id, set()))

# Global connection manager instance
manager = ConnectionManager()