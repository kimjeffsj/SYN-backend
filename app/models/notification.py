from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Optional

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


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    READ = "READ"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(SQLEnum(NotificationType))
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    priority = Column(
        SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL
    )
    data = Column(JSON, nullable=True)

    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    retry_count = Column(Integer, default=0)
    next_retry = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "status": self.status.value,
            "data": self.data,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }

    def mark_as_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)
        self.status = NotificationStatus.READ

    def mark_as_sent(self) -> None:
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_message: Optional[str] = None) -> None:
        self.status = NotificationStatus.FAILED
        if error_message:
            self.error_message = error_message

    def can_retry(self, max_retries: int = 5) -> bool:
        return (
            self.status != NotificationStatus.SENT
            and self.retry_count < max_retries
            and (
                self.next_retry is None or datetime.now(timezone.utc) >= self.next_retry
            )
        )

    def update_retry_info(self, error_message: Optional[str] = None) -> None:
        self.retry_count += 1
        self.next_retry = datetime.now(timezone.utc) + timedelta(
            minutes=min(30, 2**self.retry_count)
        )
        if error_message:
            self.error_message = error_message

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, status={self.status})>"
