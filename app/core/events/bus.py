import logging
from contextlib import asynccontextmanager
from typing import Callable, Dict, List

from app.core.database import get_db
from app.models.events import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event):
        logger.info(f"Publishing event: {event.type}")
        if event.type in self._handlers:
            db = next(get_db())
            try:
                for handler in self._handlers[event.type]:
                    logger.info(
                        f"Executing handler: {handler.__name__} for event: {event.type}"
                    )
                    await handler(event, db)
            finally:
                db.close()
        else:
            logger.warning(f"No handlers found for event type: {event.type}")


event_bus = EventBus()
