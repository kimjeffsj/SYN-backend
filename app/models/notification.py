from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    SCHEDULE = "schedule"
    ANNOUNCEMENT = "announcement"
    REQUEST = "request"


class Notification(Base):
    """Notification model for alerts"""

    __tablename__ = "notifications"
    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = Column(Enum(NotificationType))
    message: Mapped[str] = Column(String)
    is_read: Mapped[bool] = Column(Boolean, default=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
