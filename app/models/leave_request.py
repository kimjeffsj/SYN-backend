from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class LeaveType(str, PyEnum):
    VACATION = "VACATION"
    ON_LEAVE = "ON_LEAVE"


class LeaveStatus(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LeaveRequest(Base):
    """Leave Request Model"""

    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    leave_type: Mapped[str] = mapped_column(Enum(LeaveType), nullable=False)
    start_date: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(Enum(LeaveStatus), default=LeaveStatus.PENDING)

    # Admin Response
    admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    admin_comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # TimeStamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    employee = relationship(
        "User", foreign_keys=[employee_id], back_populates="leave_requests"
    )
    admin = relationship("User", foreign_keys=[admin_id])

    @property
    def duration_days(self) -> int:
        """Calculate leave duration in days"""
        return (self.end_date - self.start_date).days + 1

    def approve(self, admin_id: int, comment: Optional[str] = None) -> None:
        """Approve leave request"""
        self.status = LeaveStatus.APPROVED
        self.admin_id = admin_id
        self.admin_comment = comment
        self.processed_at = datetime.now()

    def reject(self, admin_id: int, comment: Optional[str] = None) -> None:
        """Reject leave request"""
        self.status = LeaveStatus.REJECTED
        self.admin_id = admin_id
        self.admin_comment = comment
        self.processed_at = datetime.now()

    def cancel(self) -> None:
        """Cancel leave request"""
        self.status = LeaveStatus.CANCELLED
