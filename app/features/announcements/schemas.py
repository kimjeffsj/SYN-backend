from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnnouncementBase(BaseModel):
    title: str
    content: str
    priority: str = "normal"  # normal | high


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(AnnouncementBase):
    pass


class AnnouncementResponse(AnnouncementBase):
    id: int
    create_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: dict
    read_count: int
    is_read: bool


class AnnouncementList(BaseModel):
    items: list[AnnouncementResponse]
    total: int
    unread: int
