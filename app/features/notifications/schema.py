from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from backend.app.models.notification import NotificationPriority, NotificationType


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[dict] = None


class NotificationResponse(BaseModel):
    id: int
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    data: Optional[dict] = None
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread: int
