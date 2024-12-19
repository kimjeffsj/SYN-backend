from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.features.shift_trade.schemas import (
    ShiftTradeCreate,
    ShiftTradeResponse,
    TradeResponseCreate,
    TradeResponseInfo,
    TradeResponseUpdate,
)
from app.features.shift_trade.service import ShiftTradeService
from app.models.shift_trade import TradeType
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException
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
    return ShiftTradeService.get_trade_requests(db, status, type, search)


@router.get("/{trade_id}", response_model=ShiftTradeResponse)
async def get_trade_request(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific trade request details"""
    return ShiftTradeService.get_trade_request(db, trade_id)


@router.post("/", response_model=ShiftTradeResponse)
async def create_trade_request(
    request: ShiftTradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new trade request"""
    return await ShiftTradeService.create_trade_request(
        db, request.model_dump(), current_user.id
    )


@router.post("/{trade_id}/responses", response_model=TradeResponseInfo)
async def create_trade_response(
    trade_id: int,
    response: TradeResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Respond to a trade request"""
    return await ShiftTradeService.create_trade_response(
        db, trade_id, response.model_dump(), current_user.id
    )


@router.get("/{trade_id}/check-availability")
async def check_trade_availability(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if current user can take this shift"""
    trade_request = ShiftTradeService.get_trade_request(db, trade_id)
    is_available = await ShiftTradeService.check_schedule_availability(
        db, current_user.id, trade_request.original_shift
    )
    return {"is_available": is_available}


@router.patch(
    "/{trade_id}/responses/{response_id}/status", response_model=TradeResponseInfo
)
async def update_response_status(
    trade_id: int,
    response_id: int,
    update: TradeResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update trade response status (accept/reject)"""
    return await ShiftTradeService.update_response_status(
        db, trade_id, response_id, update.status, current_user.id
    )


@router.post("/{trade_id}/accept-giveaway")
async def accept_giveaway(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a shift giveaway"""
    trade_request = ShiftTradeService.get_trade_request(db, trade_id)

    if trade_request.type != TradeType.GIVEAWAY:
        raise HTTPException(
            status_code=400, detail="This endpoint is only for giveaways"
        )

    # Check conflicts
    if not await ShiftTradeService.check_schedule_availability(
        db, current_user.id, trade_request.original_shift
    ):
        raise HTTPException(
            status_code=400, detail="You have a conflict with this shift"
        )
    return await ShiftTradeService.process_giveaway(db, trade_request, current_user.id)


@router.delete("/{trade_id}/cancel")
async def cancel_trade_request(
    trade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a trade request"""
    return await ShiftTradeService.cancel_trade_request(db, trade_id, current_user.id)
