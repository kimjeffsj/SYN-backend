from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.features.shift_trade.schemas import (
    ShiftTradeCreate,
    ShiftTradeResponse,
    TradeResponseCreate,
    TradeResponseUpdate,
)
from app.features.shift_trade.service import ShiftTradeService
from app.models.user import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(tags=["Shift Trade"])


@router.get("/", response_model=List[ShiftTradeResponse])
async def get_trade_requests(
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all trade requests with optional filtering"""
    service = ShiftTradeService(db)
    params = {"status": status, "type": type} if status or type else None
    return await service.get_trade_requests(params)


@router.get("/{trade_id}", response_model=ShiftTradeResponse)
async def get_trade_request(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific trade request details"""
    service = ShiftTradeService(db)
    return await service.get_trade_request(trade_id)


@router.post("/", response_model=ShiftTradeResponse)
async def create_trade_request(
    request: ShiftTradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new trade request"""
    service = ShiftTradeService(db)
    return await service.create_trade_request(request.model_dump(), current_user.id)


@router.post("/{trade_id}/responses", response_model=ShiftTradeResponse)
async def create_trade_response(
    trade_id: int,
    response: TradeResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Respond to a trade request"""
    service = ShiftTradeService(db)
    return await service.create_trade_response(
        trade_id, response.model_dump(), current_user.id
    )


@router.patch("/{trade_id}/responses/{response_id}/status")
async def update_response_status(
    trade_id: int,
    response_id: int,
    update: TradeResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update trade response status (accept/reject)"""
    service = ShiftTradeService(db)
    return await service.update_response_status(
        trade_id,
        response_id,
        update.status,
        current_user.id,
    )


@router.delete("/{trade_id}/cancel")
async def cancel_trade_request(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a trade request"""
    service = ShiftTradeService(db)
    await service.cancel_trade_request(trade_id, current_user.id)
    return {"message": "Trade request cancelled successfully"}
