import asyncio
import logging
from typing import Any, Dict, Optional, Set

from app.features.notifications.ws.connection import (
    ConnectionState,
    WebSocketConnection,
)
from app.features.notifications.ws.protocols import WSProtocol
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, ping_interval: int = 30, cleanup_interval: int = 60):
        self.active_connections: Dict[int, WebSocketConnection] = {}
        self.protocols: Dict[int, WSProtocol] = {}
        self.ping_interval = ping_interval
        self.cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_connections())
        self._ping_task = asyncio.create_task(self._ping_active_connections())
        logger.info("Connection manager started")

    async def stop(self) -> None:
        """Stop background tasks and cleanup connections"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._ping_task:
            self._ping_task.cancel()

        # Disconnect all clients
        for user_id in list(self.active_connections.keys()):
            await self.disconnect(user_id)

        logger.info("Connection manager stopped")

    async def connect(self, user_id: int, websocket: WebSocket) -> bool:
        """Establish new WebSocket connection"""
        try:
            # Disconnect existing connection if any
            if user_id in self.active_connections:
                await self.disconnect(user_id)

            connection = WebSocketConnection(websocket, user_id)
            connected = await connection.connect()

            if connected:
                self.active_connections[user_id] = connection
                self.protocols[user_id] = WSProtocol(connection)
                logger.info(f"New connection established for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to establish connection for user {user_id}: {str(e)}")
            return False

    async def disconnect(self, user_id: int) -> None:
        """Disconnect and cleanup WebSocket connection"""
        if user_id in self.active_connections:
            try:
                connection = self.active_connections[user_id]
                await connection.disconnect()
                logger.info(f"Connection closed for user {user_id}")
            except Exception as e:
                logger.error(f"Error disconnecting user {user_id}: {str(e)}")
            finally:
                self.active_connections.pop(user_id, None)
                self.protocols.pop(user_id, None)

    async def send_notification(
        self, user_id: int, notification: Dict[str, Any]
    ) -> bool:
        """Send notification to specific user"""
        if user_id not in self.active_connections:
            return False

        try:
            protocol = self.protocols[user_id]
            await protocol.notify(notification)
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
            await self.handle_connection_error(user_id, e)
            return False

    async def broadcast(
        self, message: Dict[str, Any], exclude: Set[int] = None
    ) -> None:
        """Broadcast message to all connected users except excluded ones"""
        exclude = exclude or set()
        for user_id in list(self.active_connections.keys()):
            if user_id not in exclude:
                await self.send_notification(user_id, message)

    async def handle_connection_error(self, user_id: int, error: Exception) -> None:
        """Handle connection errors"""
        logger.error(f"Connection error for user {user_id}: {str(error)}")
        await self.disconnect(user_id)

    def get_connection_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get connection status for a user"""
        if user_id in self.active_connections:
            connection = self.active_connections[user_id]
            return {
                "state": connection.state,
                "last_activity": connection.last_ping,
                "is_alive": connection.is_alive(),
            }
        return None

    async def _cleanup_inactive_connections(self) -> None:
        """Periodically cleanup inactive connections"""
        while True:
            try:
                for user_id, connection in list(self.active_connections.items()):
                    if not connection.is_alive():
                        logger.warning(
                            f"Cleaning up inactive connection for user {user_id}"
                        )
                        await self.disconnect(user_id)

                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(self.cleanup_interval)

    async def _ping_active_connections(self) -> None:
        """Periodically ping active connections"""
        while True:
            try:
                for user_id, connection in list(self.active_connections.items()):
                    if connection.state == ConnectionState.CONNECTED:
                        await connection.send_ping()

                await asyncio.sleep(self.ping_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ping task: {str(e)}")
                await asyncio.sleep(self.ping_interval)

    def get_active_connections_count(self) -> int:
        """Get count of active connections"""
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "active_connections": sum(
                1 for conn in self.active_connections.values() if conn.is_alive()
            ),
            "connections_by_state": {
                state.value: sum(
                    1
                    for conn in self.active_connections.values()
                    if conn.state == state
                )
                for state in ConnectionState
            },
        }


# Global instance
notification_manager = ConnectionManager()
