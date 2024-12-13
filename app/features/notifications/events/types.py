from app.core.events.base import BaseEventType


class NotificationEventType(BaseEventType):
    SCHEDULE_UPDATED = "schedule_updated"
    TRADE_REQUESTED = "trade_requested"
    TRADE_RESPONDED = "trade_responded"
    ANNOUNCEMENT_CREATED = "announcement_created"
