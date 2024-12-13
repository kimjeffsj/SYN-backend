from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    priority = Column(String, default="normal")  # normal, high
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", foreign_keys=[created_by], backref="announcements")
    read_by = relationship(
        "User", secondary="announcement_reads", backref="read_announcements"
    )

    @property
    def read_count(self) -> int:
        return len(self.read_by)

    def is_read_by(self, user_id: int) -> bool:
        return any(user.id == user_id for user in self.read_by)

    def to_response(self, user_id: int = None) -> dict:
        """Convert to response format"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "priority": self.priority,
            "created_by": self.created_by,
            "author": {
                "id": self.author.id if self.author else None,
                "name": self.author.full_name if self.author else None,
                "position": self.author.position if self.author else None,
            },
            "read_count": self.read_count,
            "is_read": self.is_read_by(user_id) if user_id else False,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


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
