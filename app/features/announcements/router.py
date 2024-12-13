from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin_user, get_current_user
from app.features.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementList,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from app.features.announcements.service import AnnouncementService
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(tags=["Announcements"])


@router.get("/", response_model=AnnouncementList)
async def get_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    priority: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all announcements"""
    return await AnnouncementService.get_announcements(
        db, current_user.id, skip, limit, priority, search
    )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific announcement"""
    announcement = await AnnouncementService.get_announcement(
        db, announcement_id, current_user.id
    )
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.post("/", response_model=AnnouncementResponse)
async def create_announcement(
    announcement: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new announcement (admin only)"""
    return await AnnouncementService.create_announcement(
        db, announcement, current_user.id
    )


@router.patch("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update an announcement (admin only)"""
    updated = await AnnouncementService.update_announcement(
        db, announcement_id, announcement_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return updated


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete an announcement (admin only)"""
    success = await AnnouncementService.delete_announcement(db, announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted successfully"}


@router.post("/{announcement_id}/read")
async def mark_as_read(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an announcement as read"""
    success = await AnnouncementService.mark_as_read(
        db, announcement_id, current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement marked as read"}
