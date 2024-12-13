from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, relationship

from .base import Base


class NotificationType(str, PyEnum):
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    SHIFT_TRADE = "SHIFT_TRADE"
    LEAVE_REQUEST = "LEAVE_REQUEST"
    SYSTEM = "SYSTEM"


class NotificationPriority(str, PyEnum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    data = Column(JSON, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="notifications")

    def mark_as_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "data": self.data,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
        }


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False, index=True)
    title_template = Column(String, nullable=False)
    message_template = Column(String, nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    notification_type = Column(Enum(NotificationType))
    enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
