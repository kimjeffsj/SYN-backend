import enum

from app.core.database import Base
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
from sqlalchemy.orm import relationship


class ShiftType(str, enum.Enum):
    """Types of work shifts"""

    MORNING = "morning"  # 0800-1600
    AFTERNOON = "afternoon"  # 1200-2000
    EVENING = "evening"  # 1700-2200
    FULL_DAY = "full_day"  # 0800-1800


class ScheduleStatus(str, enum.Enum):
    """Status of schedule"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Schedule(Base):
    """Schedule model for managing employee work schedules"""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Time information
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Shift information
    shift_type = Column(Enum(ShiftType), nullable=False)
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.PENDING)
    description = Column(String, nullable=True)

    # Repeating schedule settings
    is_repeating = Column(Boolean, default=False)
    repeat_pattern = Column(
        String, nullable=True
    )  # Format: "type|interval|days|end_date"
    parent_schedule_id = Column(
        Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="schedules")
    creator = relationship("User", foreign_keys=[created_by])
    parent_schedule = relationship("Schedule", remote_side=[id])

    def __repr__(self):
        return f"<Schedule {self.id}: {self.user.full_name} - {self.shift_type.value} ({self.start_time.date()})>"
