import logging
from datetime import datetime, timezone

from app.core.events.base import Event
from app.features.notifications.ws_manager import notification_manager
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User
from fastapi import HTTPException, logger
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def handle_schedule_update_notification(event: Event, db: Session) -> None:
    """Handle Schedule Update Notification"""
    try:
        schedule = event.data.get("schedule")
        notification = event.data.get("notification")

        # Check if notification already exists in event data
        if not notification:
            notification_data = {
                "user_id": schedule("user_id"),
                "type": NotificationType.SCHEDULE_CHANGE,
                "title": "Schedule Updated",
                "message": f"Your schedule for {schedule.start_time.strftime('%Y-%m-%d')} has been updated",
                "priority": NotificationPriority.HIGH,
                "data": {
                    "schedule_id": schedule.id,
                    "date": schedule.start_time.strftime("%Y-%m-%d"),
                    "time": f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}",
                    "status": schedule.status.value,
                },
                "status": NotificationStatus.PENDING,
            }

            notification = Notification(**notification_data)
            db.add(notification)
            db.flush()

        # Send real-time notification
        sent = await notification_manager.send_notification(
            schedule["user_id"], notification.to_dict()
        )

        if sent:
            notification.mark_as_sent()

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process schedule update notification: {str(e)}",
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
            db.flush()

            sent = await notification_manager.send_notification(
                trade_request.author_id, notification.to_dict()
            )

            if sent:
                notification.status = "sent"
                notification.sent_at = datetime.now(timezone.utc)

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process trade response notification: {str(e)}",
        )


async def handle_new_announcement_notification(event: Event, db: Session) -> None:
    logger.info("Starting announcement notification handler")
    try:
        announcement = event.data.get("announcement")
        logger.info(
            f"Processing announcement: {announcement.id if announcement else 'None'}"
        )

        if not announcement:
            logger.error("No announcement data in event")
            return

        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"Found {len(users)} active users")

        for user in users:
            try:
                notification_data = {
                    "user_id": user.id,
                    "type": NotificationType.ANNOUNCEMENT,
                    "title": "New announcement posted",
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
                    },
                    "status": NotificationStatus.PENDING,
                }

                notification = Notification(**notification_data)
                db.add(notification)
                db.flush()

                # notification_manager가 None인지 체크
                if notification_manager:
                    sent = await notification_manager.send_notification(
                        user.id, notification.to_dict()
                    )
                    if sent:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.now(timezone.utc)
                else:
                    logger.error("notification_manager is not initialized")
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = "Notification manager not available"

            except Exception as e:
                logger.error(
                    f"Error processing notification for user {user.id}: {str(e)}"
                )
                continue

        db.commit()

    except Exception as e:
        logger.error(f"Error in handle_new_announcement_notification: {str(e)}")
        if not isinstance(db.rollback, type(None)):
            await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process announcement notification: {str(e)}",
        )
