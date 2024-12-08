from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base


class TradeType(str, PyEnum):
    TRADE = "TRADE"
    GIVEAWAY = "GIVEAWAY"


class TradeStatus(str, PyEnum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class UrgencyLevel(str, PyEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ShiftTrade(Base):
    """Shift Trade Request"""

    __tablename__ = "shift_trades"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    type: Mapped[str] = Column(Enum(TradeType), nullable=False)
    author_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Original Shift Info
    original_shift_id: Mapped[int] = Column(
        ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False
    )
    preferred_shift_id: Mapped[Optional[int]] = Column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    reason: Mapped[str] = Column(String, nullable=True)
    status: Mapped[str] = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    urgency: Mapped[str] = Column(Enum(UrgencyLevel), default=UrgencyLevel.MEDIUM)

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    author = relationship("User", backref="trade_requests")
    original_shift = relationship("Schedule", foreign_keys=[original_shift_id])
    preferred_shift = relationship("Schedule", foreign_keys=[preferred_shift_id])
    responses = relationship("ShiftTradeResponse", back_populates="trade_request")


class ShiftTradeResponse(Base):
    """Shift Trade Response"""

    __tablename__ = "shift_trade_responses"

    id: Mapped[int] = Column(Integer, primary_key=True)
    trade_request_id: Mapped[int] = Column(
        ForeignKey("shift_trades.id", ondelete="CASCADE")
    )
    respondent_id: Mapped[int] = Column(ForeignKey("users.id", ondelete="CASCADE"))
    offered_shift_id: Mapped[int] = Column(
        ForeignKey("schedules.id", ondelete="CASCADE")
    )

    content: Mapped[str] = Column(String, nullable=True)
    status: Mapped[str] = Column(
        String, default="PENDING"
    )  # PENDING, ACCEPTED, REJECTED

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    trade_request = relationship("ShiftTrade", back_populates="responses")
    respondent = relationship("User", backref="trade_responses")
    offered_shift = relationship("Schedule")
