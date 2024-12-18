from app.features.shift_trade.handlers.base_handler import BaseTradeHandler
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.shift_trade import (
    ResponseStatus,
    ShiftTrade,
    ShiftTradeResponse,
    TradeStatus,
    TradeType,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class ShiftTradeHandler(BaseTradeHandler):
    def __init__(self, db: Session):
        super().__init__(db)

    async def validate(self, trade_request: ShiftTrade) -> bool:
        """
        Validate trade request
        - Check if original schedule belongs to user
        - Check if schedule is available for trade
        """
        if not await self.check_schedule_availability(
            trade_request.original_shift, trade_request.author_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule is not available for trade",
            )

        return True

    async def process(self, trade_request: ShiftTrade) -> ShiftTrade:
        """process trade request"""
        try:
            trade_request.status = TradeStatus.OPEN
            trade_request.type = TradeType.TRADE

            self.db.add(trade_request)
            await self.db.flush()
            await self.db.commit()

            return trade_request

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process trade request: {str(e)}",
            )

    async def process_response(
        self,
        trade_request: ShiftTrade,
        response: ShiftTradeResponse,
    ) -> ShiftTradeResponse:
        """
        Process response to trade request
        - Accept: Swap schedules between users
        - Reject: Keep schedules with original users
        """
        try:
            if response.status == ResponseStatus.ACCEPTED:
                # Check conflicts for both users
                if not (
                    await self.check_schedule_conflicts(
                        response.offered_shift, trade_request.author_id
                    )
                    and await self.check_schedule_conflicts(
                        trade_request.original_shift, response.respondent_id
                    )
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Schedule conflict detected",
                    )

                # Swap schedules
                original_user_id = trade_request.original_shift.user_id
                trade_request.original_shift.user_id = response.respondent_id
                response.offered_shift.user_id = original_user_id
                trade_request.status = TradeStatus.COMPLETED

                # Create notifications for both users
                notifications = [
                    Notification(
                        user_id=trade_request.author_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Shift Trade Completed",
                        message="Your Shift Trade has been successfully completed",
                        priority=NotificationPriority.HIGH,
                        data={
                            "trade_id": trade_request.id,
                            "new_schedule_id": response.offered_shift.id,
                        },
                    ),
                    Notification(
                        user_id=response.respondent_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Shift Trade Completed",
                        message="Your Shift Trade has been successfully completed",
                        priority=NotificationPriority.HIGH,
                        data={
                            "trade_id": trade_request.id,
                            "new_schedule_id": trade_request.original_shift_id,
                        },
                    ),
                ]
                self.db.add_all(notifications)

            await self.db.commit()
            return response

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process trade response: {str(e)}",
            )

    async def cancel(self, trade_request: ShiftTrade) -> ShiftTrade:
        """Cancel trade request"""
        try:
            if trade_request.status == TradeStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel completed trade request",
                )

            trade_request.status = TradeStatus.CANCELLED

            notifications = [
                Notification(
                    user_id=trade_request.author_id,
                    type=NotificationType.SHIFT_TRADE,
                    title="Shift Trade Cancelled",
                    message="A trade request you responded to has been cancelled",
                    priority=NotificationPriority.HIGH,
                    data={"trade_id": trade_request.id},
                )
                for response in trade_request.responses
            ]
            self.db.add_all(notifications)

            await self.db.commit()
            return trade_request

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel trade request: {str(e)}",
            )
