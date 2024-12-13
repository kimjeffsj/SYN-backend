import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.ping_interval: int = 30  # seconds
        self.connection_timeouts: Dict[int, datetime] = {}
        self.reconnection_attempts: Dict[int, int] = {}
        self.max_reconnection_attempts: int = 5
        self._cleanup_task: Optional[asyncio.Task] = None

    async def connect(self, user_id: int, websocket: WebSocket) -> bool:
        """Establish WebSocket connection for a user"""
        try:
            await websocket.accept()

            # If user already has a connection, close it
            if user_id in self.active_connections:
                await self.disconnect(user_id)

            self.active_connections[user_id] = websocket
            self.connection_timeouts[user_id] = datetime.now() + timedelta(
                seconds=self.ping_interval * 2
            )
            self.reconnection_attempts[user_id] = 0

            # Start ping-pong for this connection
            asyncio.create_task(self._ping_connection(user_id))

            # Ensure cleanup task is running
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(
                    self._cleanup_inactive_connections()
                )

            logger.info(
                f"User {user_id} connected. Active connections: {len(self.active_connections)}"
            )
            return True

        except Exception as e:
            logger.error(f"Error establishing connection for user {user_id}: {str(e)}")
            return False

    async def disconnect(self, user_id: int) -> None:
        """Disconnect a user's WebSocket connection"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except Exception as e:
                logger.error(f"Error closing connection for user {user_id}: {str(e)}")
            finally:
                del self.active_connections[user_id]
                self.connection_timeouts.pop(user_id, None)
                logger.info(
                    f"User {user_id} disconnected. Active connections: {len(self.active_connections)}"
                )

    async def send_notification(self, user_id: int, message: dict) -> bool:
        """Send notification to a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"No active connection for user {user_id}")
            return False

        try:
            await self.active_connections[user_id].send_json(message)
            return True
        except WebSocketDisconnect:
            await self.handle_disconnect(user_id)
            return False
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            return False

    async def broadcast(self, message: dict, exclude: Set[int] = None) -> None:
        """Broadcast message to all connected users except excluded ones"""
        exclude = exclude or set()
        for user_id in list(self.active_connections.keys()):
            if user_id not in exclude:
                await self.send_notification(user_id, message)

    async def handle_disconnect(self, user_id: int) -> None:
        """Handle disconnection with reconnection attempt tracking"""
        await self.disconnect(user_id)

        self.reconnection_attempts[user_id] = (
            self.reconnection_attempts.get(user_id, 0) + 1
        )
        if self.reconnection_attempts[user_id] <= self.max_reconnection_attempts:
            logger.info(
                f"User {user_id} disconnected. Attempt {self.reconnection_attempts[user_id]}/{self.max_reconnection_attempts}"
            )
        else:
            logger.warning(f"User {user_id} exceeded max reconnection attempts")
            self.reconnection_attempts.pop(user_id, None)

    async def _ping_connection(self, user_id: int) -> None:
        """Send periodic ping to maintain connection"""
        while user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json({"type": "ping"})
                self.connection_timeouts[user_id] = datetime.now() + timedelta(
                    seconds=self.ping_interval * 2
                )
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.error(f"Ping failed for user {user_id}: {str(e)}")
                await self.handle_disconnect(user_id)
                break

    async def _cleanup_inactive_connections(self) -> None:
        """Cleanup inactive connections periodically"""
        while True:
            try:
                current_time = datetime.now()
                for user_id, timeout in list(self.connection_timeouts.items()):
                    if current_time > timeout:
                        logger.warning(f"Connection timeout for user {user_id}")
                        await self.handle_disconnect(user_id)
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(self.ping_interval)


# Global instance
notification_manager = ConnectionManager()
