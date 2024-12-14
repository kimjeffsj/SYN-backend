import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from app.models.user import User
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class WebSocketConnection:
    def __init__(
        self,
        websocket: WebSocket,
        user: User,
        ping_interval: int = 30,
        ping_timeout: int = 10,
    ):
        self.websocket = websocket
        self.user = user
        self.state = ConnectionState.CONNECTING
        self.last_ping = datetime.now()
        self.last_pong = datetime.now()
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.error: Optional[str] = None

    async def connect(self) -> bool:
        """Establish WebSocket connection"""
        try:
            await self.websocket.accept()
            self.state = ConnectionState.CONNECTED
            logger.info(f"WebSocket connected for user {self.user.id}")
            return True
        except Exception as e:
            self.state = ConnectionState.ERROR
            self.error = str(e)
            logger.error(
                f"WebSocket connection failed for user {self.user.id}: {str(e)}"
            )
            return False

    async def disconnect(self, code: int = 1000) -> None:
        """Close WebSocket connection"""
        try:
            self.state = ConnectionState.DISCONNECTING
            await self.websocket.close(code=code)
        except Exception as e:
            logger.error(f"Error closing WebSocket for user {self.user.id}: {str(e)}")
        finally:
            self.state = ConnectionState.DISCONNECTED

    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send notification to client"""
        if self.state != ConnectionState.CONNECTED:
            return False

        try:
            await self.websocket.send_json(
                {
                    "type": "notification",
                    "payload": notification,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error sending notification to user {self.user.id}: {str(e)}")
            await self.handle_error(e)
            return False

    async def send_ping(self) -> bool:
        """Send ping message to client"""
        if self.state != ConnectionState.CONNECTED:
            return False

        try:
            await self.websocket.send_json(
                {"type": "ping", "timestamp": datetime.now().isoformat()}
            )
            self.last_ping = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error sending ping to user {self.user.id}: {str(e)}")
            await self.handle_error(e)
            return False

    async def handle_pong(self) -> None:
        """Handle pong message from client"""
        self.last_pong = datetime.now()

    async def handle_error(self, error: Exception) -> None:
        """Handle connection error"""
        self.state = ConnectionState.ERROR
        self.error = str(error)
        logger.error(f"WebSocket error for user {self.user.id}: {str(error)}")
        await self.disconnect(code=1011)  # 1011 = Server error

    def is_alive(self) -> bool:
        """Check if connection is alive based on ping/pong"""
        if self.state != ConnectionState.CONNECTED:
            return False

        timeout = self.last_ping + timedelta(seconds=self.ping_timeout)
        return datetime.now() <= timeout

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status information"""
        return {
            "user_id": self.user.id,
            "state": self.state,
            "last_ping": self.last_ping.isoformat(),
            "last_pong": self.last_pong.isoformat(),
            "is_alive": self.is_alive(),
            "error": self.error,
        }

    async def handle_message(self, message: str) -> None:
        """Handle incoming messages from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "pong":
                await self.handle_pong()
            # Add more message type handlers as needed

        except json.JSONDecodeError:
            logger.warning(f"Invalid message format from user {self.user.id}")
        except Exception as e:
            await self.handle_error(e)
