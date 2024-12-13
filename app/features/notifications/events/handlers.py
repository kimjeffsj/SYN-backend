from app.core.events.base import Event
from app.core.events.bus import event_bus

from ..service import NotificationService
from .types import NotificationEventType


async def handle_schedule_update(event: Event):
    """Handle schedule update event"""
    notification_data = {
        "user_id": event.data["user_id"],
        "type": "SCHEDULE_CHANGE",
        "title": "Schedule Updated",
        "message": f"Your schedule for {event.data['date']} has been updated",
        "data": event.data,
    }
    await NotificationService.create_notification(notification_data)


# Register handlers
event_bus.subscribe(NotificationEventType.SCHEDULE_UPDATED, handle_schedule_update)
