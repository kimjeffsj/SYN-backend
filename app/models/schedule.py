from datetime import datetime
from typing import TYPE_CHECKING, Optional

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .schedule_enums import RepeatFrequency, ScheduleStatus, ShiftType

if TYPE_CHECKING:
    from .user import User


class Schedule(Base):
    """Schedule model for managing employee work schedules"""

    __tablename__ = "schedules"

    # Primary fields
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)

    # User relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )

    # Time information
    start_time: Mapped[datetime] = Column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)

    # Schedule details
    shift_type: Mapped[ShiftType] = Column(Enum(ShiftType), nullable=False)
    status: Mapped[ScheduleStatus] = Column(
        Enum(ScheduleStatus), default=ScheduleStatus.PENDING
    )
    description: Mapped[Optional[str]] = Column(String, nullable=True)

    # Repeat settings
    is_repeating: Mapped[bool] = Column(Boolean, default=False)
    repeat_frequency: Mapped[Optional[RepeatFrequency]] = Column(
        Enum(RepeatFrequency), nullable=True
    )
    repeat_interval: Mapped[Optional[int]] = Column(Integer, nullable=True)
    repeat_days: Mapped[Optional[str]] = Column(
        String, nullable=True, comment="Comma-separated days for weekly repeat (0-6)"
    )
    repeat_end_date: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )

    # Parent-child relationship for recurring schedules
    parent_schedule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="schedules", foreign_keys=[user_id]
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    parent_schedule: Mapped[Optional["Schedule"]] = relationship(
        "Schedule", remote_side=[id], backref="child_schedules"
    )

    def __repr__(self) -> str:
        return (
            f"<Schedule {self.id}: "
            f"{self.user_id} - "  # Changed from user.full_name to user_id to avoid potential issues
            f"{self.shift_type.value} "
            f"({self.start_time.date()})"
            f"{' [Recurring]' if self.is_repeating else ''}>"
        )

    @property
    def duration_minutes(self) -> int:
        """Calculate schedule duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def is_active(self) -> bool:
        """Check if schedule is currently active"""
        now = datetime.now(self.start_time.tzinfo)
        return (
            self.status == ScheduleStatus.CONFIRMED
            and self.start_time <= now <= self.end_time
        )

    def cancel(self) -> None:
        """Cancel this schedule"""
        self.status = ScheduleStatus.CANCELLED
        self.updated_at = datetime.now(self.start_time.tzinfo)

    def complete(self) -> None:
        """Mark this schedule as completed"""
        self.status = ScheduleStatus.COMPLETED
        self.updated_at = datetime.now(self.start_time.tzinfo)
