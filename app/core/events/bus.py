from typing import Callable, Dict, List

from app.models.events import Event, EventType


class EventBus:
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Event):
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                await handler(event)


event_bus = EventBus()
