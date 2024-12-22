from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base
from .leave_request import LeaveRequest
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

    # For Demo
    is_demo: Mapped[bool] = Column(Boolean, default=False)

    # Profile fields
    department: Mapped[str] = Column(String, nullable=True)
    position: Mapped[str] = Column(String, nullable=True)
    avatar: Mapped[Optional[str]] = Column(String, nullable=True)
    comment: Mapped[Optional[str]] = Column(String, nullable=True)

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

    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        foreign_keys="[LeaveRequest.employee_id]",
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

    trade_requests = relationship("ShiftTrade", back_populates="author")
    read_announcements = relationship(
        "Announcement", secondary="announcement_reads", back_populates="read_by"
    )

    def get_current_month_stats(self) -> dict:
        """Get statistics for the current month"""
        # Get current month's first and last day
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate total hours worked this month
        monthly_hours = sum(
            (schedule.end_time - schedule.start_time).total_seconds() / 3600
            for schedule in self.schedules
            if (schedule.start_time >= month_start and schedule.status == "completed")
        )

        # Calculate total working days this month
        worked_days = len(
            set(
                schedule.start_time.date()
                for schedule in self.schedules
                if (
                    schedule.start_time >= month_start
                    and schedule.status == "completed"
                )
            )
        )

        return {"monthly_hours": round(monthly_hours, 1), "worked_days": worked_days}

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"
