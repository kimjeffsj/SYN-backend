from typing import List, Optional

from app.features.shift_trade import schemas
from app.models.shift_trade import ShiftTrade, ShiftTradeResponse, TradeStatus
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class ShiftTradeService:
    @staticmethod
    async def create_trade_request(
        db: Session, trade_data: schemas.ShiftTradeCreate, author_id: int
    ) -> ShiftTrade:
        """Create New Shift Trade request"""
        trade_request = ShiftTrade(
            **trade_data.model_dump(), author_id=author_id, status=TradeStatus.OPEN
        )

        try:
            db.add(trade_request)
            db.commit()
            db.refresh(trade_request)
            return trade_request

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def get_trade_requests(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[ShiftTrade]:
        """Get Shift Trade request list"""
        query = db.query(ShiftTrade)

        if status:
            query = query.filter(ShiftTrade.status == status)
        if type:
            query = query.filter(ShiftTrade.type == type)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def response_to_trade(
        db: Session,
        trade_id: int,
        response_data: schemas.ShiftTradeResponseCreate,
        respondent_id: int,
    ) -> ShiftTradeResponse:
        """Response to a shift trade request"""
        # Check if already responded
        existing_response = (
            db.query(ShiftTradeResponse)
            .filter(
                ShiftTradeResponse.trade_request_id == trade_id,
                ShiftTradeResponse.respondent_id == respondent_id,
            )
            .first()
        )

        if existing_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already responded to this trade request",
            )

        response = ShiftTradeResponse(
            trade_request_id=trade_id,
            respondent_id=respondent_id,
            **response_data.model_dump()
        )

        try:
            db.add(response)
            db.commit()
            db.refresh(response)
            return response
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def approve_trade_response(
        db: Session, trade_id, int, response_id: int, user_id: int
    ) -> ShiftTrade:
        """Accept Shift Trade"""
        trade = db.query(ShiftTrade).filter(ShiftTrade.id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade request not found")

        if trade.author_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        response = db.query(ShiftTradeResponse).get(response_id)
        if not response:
            raise HTTPException(status_code=404, detail="Trade response not found")

        try:
            # Update response status
            response.status = "ACCEPTED"

            # Update trade request status
            trade.status = TradeStatus.COMPLETED

            # TODO: Implement actual schedule swapping logic

            db.commit()
            return trade

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
