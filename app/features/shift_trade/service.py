from typing import List, Optional

from app.features.shift_trade.handlers.giveaway_handler import GiveawayHandler
from app.features.shift_trade.handlers.shift_trade_handler import ShiftTradeHandler
from app.models.schedule import Schedule
from app.models.shift_trade import (
    ShiftTrade,
    ShiftTradeResponse,
    TradeStatus,
    TradeType,
)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class ShiftTradeService:
    def __init__(self, db: Session):
        self.db = db
        self.handlers = {
            TradeType.GIVEAWAY: GiveawayHandler(db),
            TradeType.TRADE: ShiftTradeHandler(db),
        }

    async def create_trade_request(self, trade_data: dict, user_id: int) -> ShiftTrade:
        """Create new trade request"""
        try:
            print(f"creating trade request: {trade_data}")

            schedule = (
                self.db.query(Schedule)
                .filter(Schedule.id == trade_data["original_shift_id"])
                .first()
            )
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
                )

            trade_request = ShiftTrade(
                author_id=user_id, original_shift=schedule, **trade_data
            )

            print(f"Created trade request object: {trade_request}")
            print(f"Trade request original : {trade_request.original_shift}")

            handler = self.handlers[trade_data["type"]]
            print(f"Handler: {handler}")
            await handler.validate(trade_request)
            return await handler.process(trade_request)

        except Exception as e:
            print(f"Failed to create trade request: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create trade request: {str(e)}",
            )

    async def create_trade_response(
        self,
        trade_id: int,
        response_data: dict,
        respondent_id: int,
    ) -> ShiftTrade:
        """Create response to trade request"""
        try:

            trade_request = await self.get_trade_request(trade_id)

            if trade_request.status != TradeStatus.OPEN:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Trade request is not open for responses",
                )

            response = ShiftTradeResponse(
                trade_request_id=trade_id, respondent_id=respondent_id, **response_data
            )

            handler = self.handlers[trade_request.type]
            return await handler.process_response(trade_request, response)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create trade response: {str(e)}",
            )

    async def get_trade_request(self, trade_id: int) -> Optional[ShiftTrade]:
        """Get specific trade request"""
        trade_request = (
            self.db.query(ShiftTrade).filter(ShiftTrade.id == trade_id).first()
        )

        if not trade_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade request not found",
            )

        return trade_request

    async def get_trade_requests(
        self, params: Optional[dict] = None
    ) -> List[ShiftTrade]:
        """Get all trade requests with filtering"""
        query = self.db.query(ShiftTrade)

        if params:
            if params.get("status"):
                query = query.filter(ShiftTrade.status == params["status"])
            if params.get("type"):
                query = query.filter(ShiftTrade.type == params["type"])

        return query.order_by(ShiftTrade.created_at.desc()).all()

    async def cancel_trade_request(self, trade_id: int, user_id: int) -> ShiftTrade:
        """Cancel trade request"""
        trade_request = await self.get_trade_request(trade_id)

        if trade_request.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can cancel the trade request",
            )

        handler = self.handlers[trade_request.type]
        return await handler.cancel(trade_request)

    async def update_response_status(
        self, trade_id: int, response_id: int, status: str, user_id: int
    ) -> ShiftTradeResponse:
        """Update response status"""
        trade_request = await self.get_trade_request(trade_id)

        if trade_request.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can update response status",
            )

        response = (
            self.db.query(ShiftTradeResponse)
            .filter(
                ShiftTradeResponse.id == response_id,
                ShiftTradeResponse.trade_request_id == trade_id,
            )
            .first()
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trade response not found",
            )

        response.status = status
        handler = self.handlers[trade_request.type]
        return await handler.process_response(trade_request, response)
