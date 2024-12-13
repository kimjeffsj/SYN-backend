from datetime import datetime
from typing import Optional

from app.features.announcements.schemas import AnnouncementCreate, AnnouncementUpdate
from app.models import Announcement
from app.models.announcement import AnnouncementRead
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session


class AnnouncementService:
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

        return {"items": announcements, "total": total, "unread": unread}

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
        announcement = Announcement(
            **announcement_data.model_dump(), created_by=created_by
        )

        try:
            db.add(announcement)
            db.commit()
            db.refresh(announcement)
            return announcement
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
