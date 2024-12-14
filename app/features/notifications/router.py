from app.core.database import get_db
from app.core.security import get_current_user
from app.features.notifications.schemas import NotificationList
from app.features.notifications.service import NotificationService
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(tags=["Notifications"])


@router.get("/", response_model=NotificationList)
async def get_notification(
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's notification"""
    return await NotificationService.get_user_notification(
        db, current_user.id, skip, limit, unread_only
    )


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific notification as read"""
    success = await NotificationService.mark_as_read(
        db, notification_id, current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read"""
    success = await NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
