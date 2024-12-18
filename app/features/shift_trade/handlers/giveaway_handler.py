from email import message
from re import S

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


class GiveawayHandler(BaseTradeHandler):
    def __init__(self, db: Session):
        super().__init__(db)

    async def validate(self, trade_request: ShiftTrade) -> bool:
        """
        Validate giveaway request
        - Check if schedule belongs to user
        - Check if schedule is available for giveaway
        """
        if not await self.check_schedule_availability(
            trade_request.original_shift, trade_request.author_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule is not available for giveaway",
            )

        return True

    async def process(self, trade_request: ShiftTrade) -> ShiftTrade:
        """
        Process giveaway request
        """
        try:
            trade_request.status = TradeStatus.OPEN
            trade_request.type = TradeType.GIVEAWAY

            self.db.add(trade_request)
            await self.db.flush()

            await self.send_notifications(trade_request)
            await self.db.commit()

            return trade_request

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process giveaway request: {str(e)}",
            )

    async def process_response(
        self, trade_request: ShiftTrade, response: ShiftTradeResponse
    ) -> ShiftTradeResponse:
        """
        Process response to giveaway request
        - Accept: Transfer schedule to respondent
        - Reject: Keep schedule with original user
        """
        try:
            if response.status == ResponseStatus.ACCEPTED:
                if not await self.check_schedule_conflicts(
                    trade_request.original_shift, response.respondent_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Schedule conflicts with existing schedule",
                    )

                # Transfer schedule to respondent
                trade_request.original_shift_id = response.respondent_id
                trade_request.status = TradeStatus.COMPLETED

                completion_notification = [
                    Notification(
                        user_id=trade_request.author_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Giveaway Completed",
                        message=f"Your shift has been successfully given away",
                        priority=NotificationPriority.HIGH,
                    ),
                    Notification(
                        user_id=response.respondent_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Giveaway accepted",
                        message=f"You have successfully accepted a shift",
                        priority=NotificationPriority.HIGH,
                    ),
                ]

                self.db.add_all(completion_notification)

            await self.db.commit()
            return response

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process giveaway response: {str(e)}",
            )
