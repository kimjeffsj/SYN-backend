from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.core.celery.celery_app import celery_app
from app.core.database import SessionLocal

from .service import NotificationService
from .ws_manager import notification_manager


@celery_app.task
def send_notification(user_id: int, notification_data: Dict[str, Any]):
    """Send notifications"""
    try:
        with SessionLocal() as db:
            notification = NotificationService.create_notification(
                db, notification_data
            )

            sent = notification_manager.send_notification(
                user_id, notification.to_dict()
            )

            if sent:
                notification.status = "sent"
                notification.sent_at = datetime.now(timezone.utc)
            else:
                notification.status = "failed"
                notification.retry_count = 1
                notification.next_retry = datetime.now(timezone.utc) + timedelta(
                    minutes=2
                )

            db.add(notification)
            db.commit()

            return {"success": True, "notification_id": notification.id, "sent": sent}

    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(name="notifications.retry_failed")
def retry_failed_notifications():
    """Retry failed notifications task"""
    try:
        with SessionLocal() as db:
            failed_notifications = NotificationService.get_failed_notifications(db)

            for notification in failed_notifications:
                sent = notification_manager.send_notification(
                    notification.user_id, notification.to_dict()
                )

                if sent:
                    notification.status = "sent"
                    notification.sent_at = datetime.now(timezone.utc)
                else:
                    notification.retry_count += 1
                    if notification.retry_count >= 5:
                        notification.status = "failed"
                    else:
                        notification.next_retry = datetime.now(
                            timezone.utc
                        ) + timedelta(minutes=2**notification.retry_count)

                db.add(notification)

            db.commit()
            return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task(name="notifications.cleanup_old")
def cleanup_old_notifications():
    """Old notifications cleanup task"""
    try:
        with SessionLocal() as db:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            deleted_count = NotificationService.cleanup_old_notifications(
                db, cutoff_date
            )
            return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        return {"success": False, "error": str(e)}
