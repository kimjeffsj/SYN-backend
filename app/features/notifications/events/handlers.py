from typing import Optional

from app.core.events.base import Event
from app.features.notifications.ws_manager import notification_manager
from app.models.notification import Notification, NotificationPriority, NotificationType
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.user import User


async def handle_schedule_update_notification(event: Event, db: Session) -> None:
    """Handle Schedule Update Notification

    Args:
        event: Event Data ({
            "user_id": int,
            "schedule": Schedule,
            "changes": dict,
            "is_new": bool
        })
        db: DB Session
    """
    try:
        schedule = event.data.get("schedule")
        is_new = event.data.get("is_new", False)
        changes = event.data.get("changes", {})

        if not schedule:
            return

        notification_data = {
            "user_id": schedule.user_id,
            "type": NotificationType.SCHEDULE_CHANGE,
            "title": "New Schedule" if is_new else "Schedule Update",
            "message": (
                f"A new schedule has been added for {schedule.start_time.strftime('%Y-%m-%d')}"
                if is_new
                else f"Your schedule for {schedule.start_time.strftime('%Y-%m-%d')} has been updated"
            ),
            "priority": NotificationPriority.HIGH,
            "data": {
                "schedule_id": schedule.id,
                "is_new": is_new,
                "date": schedule.start_time.strftime("%Y-%m-%d"),
                "new_time": f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}",
                "old_time": changes.get("old_time"),
                "changed_by": {
                    "id": schedule.created_by,
                    "name": schedule.creator.full_name,
                    "position": schedule.creator.position,
                },
            },
        }

        async with db.begin():
            # Create notification
            notification = Notification(**notification_data)
            db.add(notification)
            await db.flush()

            await notification_manager.send_notification(
                schedule.user_id, notification.to_dict()
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to process schedule notification: {str(e)}"
        )


async def handle_trade_response_notification(event: Event, db: Session) -> None:
    """Shift Trade notification"""
    try:
        response = event.data.get("response")
        trade_request = event.data.get("trade_request")

        if not response or not trade_request:
            return

        notification_data = {
            "user_id": trade_request.author_id,
            "type": NotificationType.SHIFT_TRADE,
            "title": "New Response to Your Trade Request",
            "message": f"{response.respondent.full_name} has responded to your shift trade request",
            "priority": NotificationPriority.HIGH,
            "data": {
                "trade_id": trade_request.id,
                "response_id": response.id,
                "respondent": {
                    "id": response.respondent.id,
                    "name": response.respondent.full_name,
                    "position": response.respondent.position,
                },
                "offered_shift": {
                    "date": response.offered_shift.start_time.strftime("%Y-%m-%d"),
                    "time": (
                        f"{response.offered_shift.start_time.strftime('%H:%M')}-"
                        f"{response.offered_shift.end_time.strftime('%H:%M')}"
                    ),
                },
            },
        }

        async with db.begin():
            notification = Notification(**notification_data)
            db.add(notification)
            await db.flush()

            await notification_manager.send_notification(
                trade_request.author_id, notification.to_dict()
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process trade response notification: {str(e)}",
        )


async def handle_new_announcement_notification(event: Event, db: Session) -> None:
    """Handle new announcement

    Args:
        event: 이벤트 데이터 ({
            "announcement": Announcement,
            "author": User
        })
        db: 데이터베이스 세션
    """
    try:
        announcement = event.data.get("announcement")
        if not announcement:
            return

        # Check active users
        users = (
            db.query(User)
            .filter(User.is_active == True, User.deleted_at.is_(None))
            .all()
        )

        for user in users:
            notification_data = {
                "user_id": user.id,
                "type": NotificationType.ANNOUNCEMENT,
                "title": "New Announcement Posted",
                "message": announcement.title,
                "priority": (
                    NotificationPriority.HIGH
                    if announcement.priority == "high"
                    else NotificationPriority.NORMAL
                ),
                "data": {
                    "announcement_id": announcement.id,
                    "title": announcement.title,
                    "preview": (
                        announcement.content[:100] + "..."
                        if len(announcement.content) > 100
                        else announcement.content
                    ),
                    "author": {
                        "id": announcement.author.id,
                        "name": announcement.author.full_name,
                        "position": announcement.author.position,
                    },
                    "created_at": announcement.created_at.isoformat(),
                    "priority": announcement.priority,
                },
            }

            async with db.begin():
                # Create notification for each user
                notification = Notification(**notification_data)
                db.add(notification)
                await db.flush()

                await notification_manager.send_notification(
                    user.id, notification.to_dict()
                )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process announcement notification: {str(e)}",
        )
