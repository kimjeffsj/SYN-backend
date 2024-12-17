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

            return {
                "id": trade_request.id,
                "type": trade_request.type,
                "author": {
                    "id": trade_request.author.id,
                    "name": trade_request.author.full_name,
                    "position": trade_request.author.position,
                },
                "original_shift": {
                    "date": trade_request.original_shift.start_time.strftime(
                        "%Y-%m-%d"
                    ),
                    "start_time": trade_request.original_shift.start_time.isoformat(),
                    "end_time": trade_request.original_shift.end_time.isoformat(),
                    "shift_type": trade_request.original_shift.shift_type,
                },
                "preferred_shift": trade_request.preferred_shift_id
                and {
                    "date": trade_request.preferred_shift.start_time.strftime(
                        "%Y-%m-%d"
                    ),
                    "time": f"{trade_request.preferred_shift.start_time.strftime('%H:%M')}-{trade_request.preferred_shift.end_time.strftime('%H:%M')}",
                    "shift_type": trade_request.preferred_shift.shift_type,
                },
                "status": trade_request.status,
                "responses": len(trade_request.responses),
                "created_at": trade_request.created_at.isoformat(),
                "reason": trade_request.reason,
                "urgency": trade_request.urgency,
            }

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def get_trade_requests(db: Session, skip: int = 0, limit: int = 100):
        try:
            query = db.query(ShiftTrade)
            trades = query.offset(skip).limit(limit).all()

            formatted_trades = []
            for trade in trades:
                if not trade or not trade.original_shift or not trade.author:
                    continue

                try:
                    formatted_trade = {
                        "id": trade.id,
                        "type": trade.type,
                        "author": {
                            "id": trade.author.id,
                            "name": trade.author.full_name,
                            "position": trade.author.position,
                        },
                        "original_shift": {
                            "start_time": trade.original_shift.start_time.isoformat(),
                            "end_time": trade.original_shift.end_time.isoformat(),
                            "shift_type": trade.original_shift.shift_type.value,
                        },
                        "status": trade.status.value,
                        "responses": len(trade.responses) if trade.responses else 0,
                        "created_at": (
                            trade.created_at.isoformat() if trade.created_at else None
                        ),
                        "reason": trade.reason,
                        "urgency": trade.urgency.value,
                    }

                    if trade.preferred_shift_id and trade.preferred_shift:
                        formatted_trade["preferred_shift"] = {
                            "start_time": trade.preferred_shift.start_time.isoformat(),
                            "end_time": trade.preferred_shift.end_time.isoformat(),
                            "shift_type": trade.preferred_shift.shift_type.value,
                        }

                    formatted_trades.append(formatted_trade)
                except Exception as e:
                    print(f"Error formatting trade {trade.id}: {str(e)}")
                    continue

            return formatted_trades
        except Exception as e:
            print(f"Error in get_trade_requests: {str(e)}")
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
    ) -> List[dict]:
        """Get Shift Trade request list"""
        try:
            query = db.query(ShiftTrade)

            if status:
                query = query.filter(ShiftTrade.status == status.upper())
            if type:
                query = query.filter(ShiftTrade.type == type.upper())

            trades = query.offset(skip).limit(limit).all()

            formatted_trades = []

            for trade in trades:
                if not trade or not trade.original_shift or not trade.author:
                    continue

                try:
                    formatted_trade = {
                        "id": trade.id,
                        "type": trade.type,
                        "author": {
                            "id": trade.author.id,
                            "name": trade.author.full_name,
                            "position": trade.author.position,
                        },
                        "original_shift": {
                            "date": trade.original_shift.start_time.strftime(
                                "%Y-%m-%d"
                            ),
                            "start_time": trade.original_shift.start_time.isoformat(),
                            "end_time": trade.original_shift.end_time.isoformat(),
                            "shift_type": trade.original_shift.shift_type,
                        },
                        "status": trade.status,
                        "responses": len(trade.responses) if trade.responses else 0,
                        "created_at": (
                            trade.created_at.isoformat() if trade.created_at else None
                        ),
                        "reason": trade.reason,
                        "urgency": trade.urgency,
                    }

                    # only if it has preferred_shift
                    if trade.preferred_shift_id and trade.preferred_shift:
                        formatted_trade["preferred_shift"] = {
                            "date": trade.preferred_shift.start_time.strftime(
                                "%Y-%m-%d"
                            ),
                            "time": f"{trade.preferred_shift.start_time.strftime('%H:%M')}-{trade.preferred_shift.end_time.strftime('%H:%M')}",
                            "shift_type": trade.preferred_shift.shift_type,
                        }
                    else:
                        formatted_trade["preferred_shift"] = None

                    formatted_trades.append(formatted_trade)
                except Exception as e:
                    print(f"Error formatting trade {trade.id}: {str(e)}")
                    continue

            return formatted_trades
        except Exception as e:
            print(f"Error in get_trade_requests: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

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
            **response_data.model_dump(),
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
