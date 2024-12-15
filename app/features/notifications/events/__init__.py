from app.core.events import event_bus

from .handlers import (
    handle_new_announcement_notification,
    handle_schedule_update_notification,
    handle_trade_response_notification,
)
from .types import NotificationEventType

__all__ = [
    "NotificationEventType",
    "handle_new_announcement_notification",
    "handle_schedule_update_notification",
    "handle_trade_response_notification",
    "register_notification_handlers",
]


def register_notification_handlers(event_bus):
    """Register all notification event handlers"""
    from .types import NotificationEventType

    event_bus.subscribe(
        NotificationEventType.SCHEDULE_UPDATED, handle_schedule_update_notification
    )
    event_bus.subscribe(
        NotificationEventType.ANNOUNCEMENT_CREATED, handle_new_announcement_notification
    )
    event_bus.subscribe(
        NotificationEventType.TRADE_RESPONDED, handle_trade_response_notification
    )
