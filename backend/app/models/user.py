from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base

if TYPE_CHECKING:
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

    # Status and security fields
    is_active: Mapped[bool] = Column(Boolean, default=True)
    requires_password_change: Mapped[bool] = Column(Boolean, default=False)
    last_password_change: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
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

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
