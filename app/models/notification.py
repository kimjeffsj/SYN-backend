from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class NotificationType(str, Enum):
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    SHIFT_TRADE = "SHIFT_TRADE"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    LEAVE_REQUEST = "LEAVE_REQUEST"
    SYSTEM = "SYSTEM"


class NotificationPriority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(SQLEnum(NotificationType))
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )
    data = Column(JSON, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "data": self.data,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
        }
