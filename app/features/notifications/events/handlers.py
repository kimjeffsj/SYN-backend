from datetime import datetime

from app.core.database import SessionLocal
from app.core.events.base import Event
from app.core.events.bus import event_bus
from app.models.notification import NotificationPriority, NotificationType
from app.models.user import User

from ..service import NotificationService
from ..ws_manager import notification_manager
from .types import NotificationEventType


async def handle_schedule_update(event: Event):
    """Handle schedule update event"""
    db = SessionLocal()
    try:
        notification_data = {
            "user_id": event.data["user_id"],
            "type": NotificationType.SCHEDULE_CHANGE,
            "title": "Schedule Updated",
            "message": f"Your schedule for {event.data['date']} has been updated",
            "priority": NotificationPriority.HIGH,
            "data": {
                "schedule_id": event.data.get("schedule_id"),
                "old_time": event.data.get("old_time"),
                "new_time": event.data.get("new_time"),
                "date": event.data["date"],
            },
        }

        notification = await NotificationService.create_notification(
            db, notification_data
        )
        await notification_manager.send_notification(
            notification.user_id, notification.to_dict()
        )

    finally:
        db.close()


async def handle_announcement_created(event: Event):
    """Handle new announcement event"""
    db = SessionLocal()
    try:
        announcement = event.data.get("announcement")
        if not announcement:
            return

        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            notification_data = {
                "user_id": user.id,
                "type": NotificationType.ANNOUNCEMENT,
                "title": "New Announcement",
                "message": announcement.title,
                "priority": announcement.priority,
                "data": {
                    "announcement_id": announcement.id,
                    "title": announcement.title,
                    "content": announcement.content,
                    "author": announcement.author.full_name,
                },
            }

            notification = await NotificationService.create_notification(
                db, notification_data
            )
            await notification_manager.send_notification(
                user.id, notification.to_dict()
            )

    finally:
        db.close()


async def handle_shift_trade_requested(event: Event):
    """Handle shift trade request event"""
    db = SessionLocal()
    try:
        trade = event.data.get("trade")
        if not trade:
            return

        notification_data = {
            "user_id": trade.target_user_id,
            "type": NotificationType.SHIFT_TRADE,
            "title": "New Shift Trade Request",
            "message": f"{trade.author.full_name} wants to trade shifts with you",
            "priority": NotificationPriority.NORMAL,
            "data": {
                "trade_id": trade.id,
                "requester": trade.author.full_name,
                "original_shift": {
                    "date": trade.original_shift.start_time.strftime("%Y-%m-%d"),
                    "time": f"{trade.original_shift.start_time.strftime('%H:%M')} - {trade.original_shift.end_time.strftime('%H:%M')}",
                },
                "preferred_shift": (
                    {
                        "date": trade.preferred_shift.start_time.strftime("%Y-%m-%d"),
                        "time": f"{trade.preferred_shift.start_time.strftime('%H:%M')} - {trade.preferred_shift.end_time.strftime('%H:%M')}",
                    }
                    if trade.preferred_shift
                    else None
                ),
            },
        }

        notification = await NotificationService.create_notification(
            db, notification_data
        )
        await notification_manager.send_notification(
            notification.user_id, notification.to_dict()
        )

    finally:
        db.close()


async def handle_leave_request(event: Event):
    """Handle leave request event"""
    db = SessionLocal()
    try:
        request = event.data.get("request")
        if not request:
            return

        # Notify admin
        notification_data = {
            "user_id": request.approver_id,
            "type": NotificationType.LEAVE_REQUEST,
            "title": "New Leave Request",
            "message": f"{request.user.full_name} has requested leave",
            "priority": NotificationPriority.NORMAL,
            "data": {
                "request_id": request.id,
                "user": request.user.full_name,
                "start_date": request.start_date.strftime("%Y-%m-%d"),
                "end_date": request.end_date.strftime("%Y-%m-%d"),
                "reason": request.reason,
            },
        }

        notification = await NotificationService.create_notification(
            db, notification_data
        )
        await notification_manager.send_notification(
            notification.user_id, notification.to_dict()
        )

    finally:
        db.close()


# Register all event handlers
event_bus.subscribe(NotificationEventType.SCHEDULE_UPDATED, handle_schedule_update)
event_bus.subscribe(
    NotificationEventType.ANNOUNCEMENT_CREATED, handle_announcement_created
)
event_bus.subscribe(NotificationEventType.TRADE_REQUESTED, handle_shift_trade_requested)
event_bus.subscribe(NotificationEventType.LEAVE_REQUESTED, handle_leave_request)
