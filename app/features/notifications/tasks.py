from datetime import datetime, timedelta, timezone

from app.core.celery.celery_app import celery_app
from app.core.database import SessionLocal

from .service import NotificationService
from .ws_manager import notification_manager


@celery_app.task
async def send_notification(user_id: int, notification_data: dict):
    """Send notifications"""
    try:

        with SessionLocal() as db:
            notification = NotificationService.create_notification(
                db, notification_data
            )

        await notification_manager.send_notification(user_id, notification.to_dict())

        return {"success": True, "notification_id": notification.id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@celery_app.task
def cleanup_old_notifications():
    """Cleanup old notifications"""
    try:
        with SessionLocal() as db:

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            deleted_count = NotificationService.cleanup_old_notifications(
                db, cutoff_date
            )
            return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        return {"success": False, "error": str(e)}
