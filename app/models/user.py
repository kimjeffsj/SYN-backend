from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
    from .notification import Notification
    from .schedule import Schedule


class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    # Primary fields
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    email: Mapped[str] = Column(String, unique=True, index=True)
    full_name: Mapped[str] = Column(String)
    hashed_password: Mapped[str] = Column(String)
    role: Mapped[str] = Column(String)  # "admin" or "employee"

    # Profile fields
    department: Mapped[Optional[str]] = Column(String, nullable=True)
    position: Mapped[Optional[str]] = Column(String, nullable=True)
    avatar: Mapped[Optional[str]] = Column(String, nullable=True)

    # Status and security fields
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_on_leave: Mapped[bool] = Column(Boolean, default=False)
    leave_balance: Mapped[int] = Column(Integer, default=0)
    total_hours_worked: Mapped[float] = Column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    last_active_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    schedules: Mapped[List["Schedule"]] = relationship(
        "Schedule",
        back_populates="user",
        primaryjoin="and_(User.id == Schedule.user_id, Schedule.deleted_at.is_(None))",
        cascade="all, delete-orphan",
    )

    created_schedules: Mapped[List["Schedule"]] = relationship(
        "Schedule",
        back_populates="creator",
        primaryjoin="User.id == Schedule.created_by",
        foreign_keys="Schedule.created_by",
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def pending_requests_count(self) -> int:
        return len([s for s in self.schedules if s.status == "pending"])

    @property
    def completed_shifts_count(self) -> int:
        return len([s for s in self.schedules if s.status == "completed"])
