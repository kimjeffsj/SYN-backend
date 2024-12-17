from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.features.shift_trade import schemas
from app.features.shift_trade.service import ShiftTradeService
from app.models.user import User
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(tags=["Shift Trade"])


@router.post("/", response_model=schemas.ShiftTradeResponse)
async def create_trade_request(
    trade_data: schemas.ShiftTradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create shift trade request"""
    return await ShiftTradeService.create_trade_request(db, trade_data, current_user.id)


@router.get("/", response_model=List[schemas.ShiftTradeResponse])
async def get_trade_requests(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Shift Trade list"""
    return await ShiftTradeService.get_trade_requests(db, skip, limit, status, type)


@router.post("/{trade_id}/responses", response_model=schemas.ShiftTradeResponseDetail)
async def respond_to_trade(
    trade_id: int,
    response_data: schemas.ShiftTradeResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Respond to shift trade"""
    print(f"Received trade response request: {trade_id}")  # 디버깅 로그 추가
    print(f"Response data: {response_data}")
    return await ShiftTradeService.response_to_trade(
        db, trade_id, response_data, current_user.id
    )


@router.post("/{trade_id}/responses/{response_id}/approve")
async def approve_trade_response(
    trade_id: int,
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept trade response"""
    return await ShiftTradeService.approve_trade_response(
        db, trade_id, response_id, current_user.id
    )
