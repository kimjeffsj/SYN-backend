from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Announcement(Base):
    """Announcement model for notices"""

    __tablename__ = "announcements"

    id: Mapped[int] = Column(Integer, primary_key=True)
    title: Mapped[str] = Column(String)
    content: Mapped[str] = Column(String)
    priority: Mapped[str] = Column(String, default="normal")  # normal, high
    created_by: Mapped[int] = Column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    read_by: Mapped[List["User"]] = relationship(
        "User", secondary="announcement_reads", backref="read_announcements"
    )


class AnnouncementRead(Base):
    """Tracks which users have read which announcements"""

    __tablename__ = "announcement_reads"

    announcement_id: Mapped[int] = Column(
        ForeignKey("announcements.id"), primary_key=True
    )
    user_id: Mapped[int] = Column(ForeignKey("users.id"), primary_key=True)
    read_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
