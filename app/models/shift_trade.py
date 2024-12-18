from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, and_, func
from sqlalchemy.orm import Mapped, relationship

from .base import Base
from .schedule import Schedule


class TradeType(str, PyEnum):
    TRADE = "TRADE"
    GIVEAWAY = "GIVEAWAY"


class TradeStatus(str, PyEnum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class UrgencyLevel(str, PyEnum):
    HIGH = "high"
    NORMAL = "normal"


class ResponseStatus(str, PyEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class ShiftTrade(Base):
    """Shift Trade Request"""

    __tablename__ = "shift_trades"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    type: Mapped[str] = Column(Enum(TradeType), nullable=False)
    author_id: Mapped[int] = Column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    original_shift_id: Mapped[int] = Column(
        ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False
    )
    preferred_shift_id: Mapped[Optional[int]] = Column(
        ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True
    )

    reason: Mapped[str] = Column(String, nullable=True)
    status: Mapped[str] = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    urgency: Mapped[str] = Column(Enum(UrgencyLevel), default=UrgencyLevel.NORMAL)

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
    responses = relationship(
        "ShiftTradeResponse",
        back_populates="trade_request",
        cascade="all, delete-orphan",
    )

    async def check_conflict(self, db_session) -> bool:
        """Check for schedule conflicts"""
        if self.type == TradeType.GIVEAWAY:
            return await self._check_giveaway_conflict(db_session)
        return await self._check_trade_conflict(db_session)

    async def _check_giveaway_conflict(self, db_session) -> bool:
        """Check conflicts for giveaway requests"""
        original_shift = await db_session.get(Schedule, self.original_shift_id)
        if not original_shift:
            return False

        # Check if the user has any existing shifts that conflict with the original shift
        existing_schedule = (
            await db_session.query(Schedule)
            .filter(
                Schedule.user_id == self.author_id,
                Schedule.id != self.original_shift_id,
                and_(
                    Schedule.start_time < original_shift.end_time,
                    Schedule.end_time > original_shift.start_time,
                ),
            )
            .first()
        )

        return existing_schedule is None

    async def _check_trade_conflict(self, db_session) -> bool:
        """Check conflicts for trade requests"""
        if not await self._check_giveaway_conflict(db_session):
            return False

        if self.preferred_shift_id:
            preferred_shift = await db_session.get(Schedule, self.preferred_shift_id)
            if not preferred_shift:
                return False

            existing_schedule = (
                await db_session.query(Schedule)
                .filter(
                    Schedule.user_id == self.author_id,
                    Schedule.id != self.preferred_shift_id,
                    and_(
                        Schedule.start_time < preferred_shift.end_time,
                        Schedule.end_time > preferred_shift.start_time,
                    ),
                )
                .first()
            )

            return existing_schedule is None

        return True


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
    status: Mapped[str] = Column(Enum(ResponseStatus), default=ResponseStatus.PENDING)

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

    async def check_conflict(self, db_session) -> bool:
        """Check for response conflicts"""
        trade_request = await db_session.get(ShiftTrade, self.trade_request_id)
        if not trade_request:
            return False

        original_shift = trade_request.original_shift
        return await self._check_schedule_conflict(
            db_session, self.respondent_id, original_shift
        )

    async def _check_schedule_conflict(
        self, db_session, user_id: int, shift: Schedule
    ) -> bool:
        """Helper method to check schedule conflicts"""
        existing_schedule = (
            await db_session.query(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.id != shift.id,
                and_(
                    Schedule.start_time < shift.end_time,
                    Schedule.end_time > shift.start_time,
                ),
            )
            .first()
        )

        return existing_schedule is None
