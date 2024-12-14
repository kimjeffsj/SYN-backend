import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.models.events import Event, EventType

from .connection import WebSocketConnection

logger = logging.getLogger(__name__)


class WSMessageType(str, Enum):
    NOTIFICATION = "notification"
    EVENT = "event"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class WSMessage:
    def __init__(
        self,
        type: WSMessageType,
        payload: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.type = type
        self.payload = payload or {}
        self.timestamp = timestamp or datetime.now()

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "WSMessage":
        return cls(
            type=WSMessageType(data["type"]),
            payload=data.get("payload"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class WSProtocol:
    def __init__(self, connection: WebSocketConnection):
        self.connection = connection
        self._event_handlers: Dict[str, List[Callable]] = {}

    async def handle_message(self, raw_message: str) -> None:
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(raw_message)
            message = WSMessage.from_json(data)

            if message.type == WSMessageType.PING:
                await self._handle_ping()
            elif message.type == WSMessageType.EVENT:
                await self._handle_event(message.payload)
            elif message.type == WSMessageType.ERROR:
                await self._handle_error(message.payload)

        except json.JSONDecodeError:
            logger.warning(
                f"Invalid message format from user {self.connection.user.id}"
            )
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.connection.handle_error(e)

    async def _handle_ping(self) -> None:
        """Handle ping message"""
        await self.send_message(WSMessage(type=WSMessageType.PONG))

    async def _handle_event(self, payload: Dict[str, Any]) -> None:
        """Handle event message"""
        try:
            event_type = EventType(payload.get("event_type"))
            handlers = self._event_handlers.get(event_type, [])

            for handler in handlers:
                await handler(Event(event_type, payload.get("data", {})))

        except Exception as e:
            logger.error(f"Error handling event: {str(e)}")

    async def _handle_error(self, payload: Dict[str, Any]) -> None:
        """Handle error message"""
        error_message = payload.get("message", "Unknown error")
        logger.error(f"Client error received: {error_message}")

    async def send_message(self, message: WSMessage) -> None:
        """Send message to client"""
        await self.connection.websocket.send_json(message.to_json())

    def add_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """Add event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """Remove event handler"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def notify(self, notification: Dict[str, Any]) -> None:
        """Send notification to client"""
        message = WSMessage(type=WSMessageType.NOTIFICATION, payload=notification)
        await self.send_message(message)
