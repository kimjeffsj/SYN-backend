from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.models.notification import Notification, NotificationType
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .schemas import NotificationCreate


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

        items = [notification.to_dict() for notification in notifications]

        return {"items": items, "total": total, "unread": unread}

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

    @staticmethod
    async def get_pending_notifications(
        db: Session,
        user_id: int,
        days: int = 15,
        notification_types: Optional[List[NotificationType]] = None,
    ) -> List[Notification]:
        """Get pending notifications for user when login"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= cutoff_date,
                    Notification.is_read == False,
                    Notification.deleted_at.is_(None),
                )
            )

            if notification_types:
                query = query.filter(Notification.type.in_(notification_types))

            notifications = query.order_by(
                Notification.priority.desc(), Notification.created_at.desc()
            ).all()

            return notifications

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch pending notifications: {str(e)}",
            )

    @staticmethod
    async def get_notification_summary(db: Session, user_id: int) -> dict:
        """Get notification summary for dashboard"""
        try:
            base_query = db.query(Notification).filter(
                Notification.user_id == user_id, Notification.deleted_at.is_(None)
            )

            total_unread = base_query.filter(Notification.is_read == False).count()

            type_summary = {}
            for ntype in Notification:
                count = base_query.filter(
                    Notification.type == ntype, Notification.is_read == False
                ).count()
                type_summary[ntype.value] = count

            return {"total_unread": total_unread, "type_summary": type_summary}

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get notification summary: {str(e)}"
            )

    @staticmethod
    async def handle_user_login(db: Session, user: User) -> dict:
        """Handle notifications when user logs in"""
        try:

            notifications = await NotificationService.get_pending_notifications(
                db, user.id
            )

            summary = await NotificationService.get_notification_summary(db, user.id)

            notification_data = {
                "notifications": [n.to_dict() for n in notifications],
                "summary": summary,
                "has_critical": any(n.priority == "HIGH" for n in notifications),
            }

            return notification_data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process login notifications: {str(e)}",
            )

    @staticmethod
    async def update_user_last_seen(db: Session, user_id: int) -> None:
        """Update user's last seen timestamp"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_active_at = datetime.now()
                db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to update last seen time: {str(e)}"
            )
