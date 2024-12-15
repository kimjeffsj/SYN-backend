import logging
from datetime import datetime
from typing import Optional

from app.core.events import event_bus
from app.core.events.base import Event
from app.features.announcements.schemas import AnnouncementCreate, AnnouncementUpdate
from app.features.notifications.events.types import NotificationEventType
from app.models import Announcement
from app.models.announcement import AnnouncementRead
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnnouncementService:
    @staticmethod
    async def format_announcement(announcement: Announcement, user_id: int) -> dict:
        """Format announcement for response"""
        return {
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "priority": announcement.priority,
            "created_by": announcement.created_by,
            "author": {
                "id": announcement.author.id if announcement.author else None,
                "name": announcement.author.full_name if announcement.author else None,
                "position": (
                    announcement.author.position if announcement.author else None
                ),
            },
            "read_count": announcement.read_count,
            "is_read": announcement.is_read_by(user_id),
            "created_at": announcement.created_at,
            "updated_at": announcement.updated_at,
        }

    @staticmethod
    async def get_announcements(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ):
        """Get all announcements"""
        query = db.query(Announcement).filter(Announcement.deleted_at.is_(None))

        if priority:
            query = query.filter(Announcement.priority == priority)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Announcement.title.ilike(search_term))
                | (Announcement.content.ilike(search_term))
            )

        total = query.count()
        unread = query.filter(~Announcement.read_by.any(User.id == user_id)).count()

        announcements = (
            query.order_by(Announcement.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Format each announcement
        items = [
            await AnnouncementService.format_announcement(ann, user_id)
            for ann in announcements
        ]

        return {"items": items, "total": total, "unread": unread}

    @staticmethod
    async def get_announcement(db: Session, announcement_id: int, user_id: int):
        """Get an announcement"""
        announcement = (
            db.query(Announcement)
            .filter(
                Announcement.id == announcement_id, Announcement.deleted_at.is_(None)
            )
            .first()
        )

        if not announcement:
            return None

        # Track read status
        if user_id not in [r.user_id for r in announcement.read_by]:
            await AnnouncementService.mark_as_read(db, announcement_id, user_id)

        return announcement

    @staticmethod
    async def create_announcement(
        db: Session, announcement_data: AnnouncementCreate, created_by: int
    ):
        """Create a new announcement"""
        print("announcement created")
        announcement = Announcement(
            **announcement_data.model_dump(), created_by=created_by
        )
        db.add(announcement)
        db.commit()
        db.refresh(announcement)

        logger.info(f"Attempting to publish announcement event: {announcement.id}")
        await event_bus.publish(
            Event(
                type=NotificationEventType.ANNOUNCEMENT_CREATED,
                data={"announcement": announcement, "author": announcement.author},
            )
        )
        logger.info(f"Successfully published announcement event: {announcement.id}")

        try:
            db.refresh(announcement)
            return {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "priority": announcement.priority,
                "created_by": announcement.created_by,
                "author": {
                    "id": announcement.author.id,
                    "name": announcement.author.full_name,
                    "position": announcement.author.position,
                },
                "read_count": 0,
                "is_read": False,
                "created_at": announcement.created_at,
                "updated_at": announcement.updated_at,
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not create announcement: {str(e)}"
            )

    @staticmethod
    async def update_announcement(
        db: Session, announcement_id: int, update_data: AnnouncementUpdate
    ):
        """Update an existing announcement"""
        announcement = (
            db.query(Announcement)
            .filter(
                Announcement.id == announcement_id, Announcement.deleted_at.is_(None)
            )
            .first()
        )

        if not announcement:
            return None

        for key, value in update_data.model_dump().items():
            setattr(announcement, key, value)

        try:
            db.commit()
            db.refresh(announcement)
            return announcement
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not update announcement: {str(e)}"
            )

    @staticmethod
    async def delete_announcement(db: Session, announcement_id: int):
        """Soft delete an announcement"""
        announcement = (
            db.query(Announcement)
            .filter(
                Announcement.id == announcement_id, Announcement.deleted_at.is_(None)
            )
            .first()
        )

        if not announcement:
            return False

        try:
            announcement.deleted_at = datetime.now()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not delete announcement: {str(e)}"
            )

    @staticmethod
    async def mark_as_read(db: Session, announcement_id: int, user_id: int):
        """Mark as read"""
        announcement = (
            db.query(Announcement)
            .filter(
                Announcement.id == announcement_id, Announcement.deleted_at.is_(None)
            )
            .first()
        )

        if not announcement:
            return False

        try:
            if user_id not in [r.user_id for r in announcement.read_by]:
                read_record = AnnouncementRead(
                    announcement_id=announcement_id, user_id=user_id
                )
                db.add(read_record)
                db.commit()

            return True

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Could not mark announcement as read: {str(e)}"
            )
