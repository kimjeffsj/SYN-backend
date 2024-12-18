from abc import ABC, abstractmethod

from app.models.schedule import Schedule
from app.models.shift_trade import ShiftTrade
from sqlalchemy.orm import Session


class BaseTradeHandler(ABC):
    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    async def validate(self, trade_request: ShiftTrade) -> bool:
        """Validate the trade request."""
        pass

    @abstractmethod
    async def process(self, trade_request: ShiftTrade) -> bool:
        """Process the trade request."""
        pass

    @abstractmethod
    async def check_schedule_availability(
        self, schedule: Schedule, user_id: int
    ) -> bool:
        """Check if the user is available for the trade."""
        if not schedule:
            return False

        existing_trade = (
            self.db.query(ShiftTrade)
            .filter(
                ShiftTrade.original_shift_id == schedule.id, ShiftTrade.status == "OPEN"
            )
            .first()
        )

        return existing_trade is None

    async def check_schedule_conflicts(self, schedule: Schedule, user_id: int) -> bool:
        """Check schedule conflicts"""
        existing_schedule = (
            self.db.query(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.id != schedule.id,
                Schedule.start_time < schedule.end_time,
                Schedule.end_time > schedule.start_time,
            )
            .first()
        )

        return existing_schedule is None

    @abstractmethod
    async def send_notifications(self, trade_request: ShiftTrade) -> None:
        """Send notifications"""
        pass
