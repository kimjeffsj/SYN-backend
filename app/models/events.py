from datetime import datetime, timezone
from enum import Enum


class EventType(str, Enum):
    SCHEDULE_CREATED = "schedule_created"
    SCHEDULE_UPDATED = "schedule_updated"
    SCHEDULE_DELETED = "schedule_deleted"
    TRADE_REQUESTED = "trade_requested"
    TRADE_RESPONDED = "trade_responded"
    TRADE_COMPLETED = "trade_completed"
    ANNOUNCEMENT_CREATED = "announcement_created"


class Even:
    def __init__(self, event_type: EventType, data: dict):
        self.type = event_type
        self.data = data
        self.timestamp = datetime.now(timezone.utc)
