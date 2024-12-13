from app.core.events.event_bus import event_bus
from app.features.notifications.service import NotificationService
from app.models.events import Event, EventType
from app.models.notification import NotificationType


async def handle_schedule_update(event: Event):
    notification_data = {
        "user_id": event.data["user_id"],
        "type": NotificationType.SCHEDULE_CHANGE,
        "title": "Schedule Updated",
        "message": f"Your schedule for {event.data['date']} has been updated",
        "data": event.data,
    }
    await NotificationService.create_notification(notification_data)


# Register handlers
event_bus.subscribe(EventType.SCHEDULE_UPDATED, handle_schedule_update)
