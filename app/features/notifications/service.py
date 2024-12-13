from datetime import datetime, timezone

from app.models.notification import Notification
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .schema import NotificationCreate


class NotificationService:
    @staticmethod
    async def create_notification(
        db: Session, notification_data: NotificationCreate
    ) -> Notification:
        """Create notification"""
        try:
            notification = Notification(**notification_data.model_dump())
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not create notification: {str(e)}"
            )

    @staticmethod
    async def get_user_notification(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
    ) -> dict:
        "Get notifications for user"
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = query.count()

        unread = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    async def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        notification = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )

        if not notification:
            return False

        try:
            notification.mark_as_read()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not mark notification as read: {str(e)}"
            )

    @staticmethod
    async def mark_all_as_read(db: Session, user_id: int) -> bool:
        """Mark all notifications as read"""
        try:
            now = datetime.now(timezone.utc)
            db.query(Notification).filter(
                Notification.user_id == user_id, Notification.is_read == False
            ).update({"is_read": True, "read_at": now})
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Could not mark all notifications as read: {str(e)}",
            )
