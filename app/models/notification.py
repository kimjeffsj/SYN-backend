from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class NotificationType(str, PyEnum):
    ANNOUNCEMENT = "announcement"
    SCHEDULE_CHANGE = "schedule_change"
    SHIFT_TRADE = "shift_trade"
    LEAVE_REQUEST = "leave_request"
    SYSTEM = "system"


class NotificationPriority(str, PyEnum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Notification(Base):
    """Notification model for alerts"""

    __tablename__ = "notifications"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: NotificationType = Column(Enum(NotificationType), nullable=False)
    title: str = Column(String, nullable=False)
    message: str = Column(String, nullable=False)
    priority: NotificationPriority = Column(
        Enum(NotificationPriority), default=NotificationPriority.NORMAL
    )
    data: dict = Column(JSON, nullable=False)
    is_read: bool = Column(Boolean, default=False)
    read_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def mark_as_read(self) -> None:
        """Mark the notification as read"""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Formatting to dict"""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "data": self.data,
            "is_read": self.is_read,
            "read_at": self.read_at,
            "created_at": self.created_at,
        }
