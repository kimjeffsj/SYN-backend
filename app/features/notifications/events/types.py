from app.core.events.base import BaseEventType


class NotificationEventType(BaseEventType):
    SCHEDULE_UPDATED = "schedule_updated"
    ANNOUNCEMENT_CREATED = "announcement_created"
    TRADE_REQUESTED = "trade_requested"
    TRADE_RESPONDED = "trade_responded"
    LEAVE_REQUESTED = "leave_requested"
    LEAVE_RESPONDED = "leave_responded"
