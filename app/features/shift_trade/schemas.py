from datetime import datetime
from typing import Optional

from app.models.shift_trade import TradeStatus, TradeType, UrgencyLevel
from pydantic import BaseModel


class ShiftTradeBase(BaseModel):
    type: TradeType
    reason: Optional[str] = None
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM


class ShiftTradeCreate(ShiftTradeBase):
    original_shift_id: int
    preferred_shift_id: Optional[int] = None


class ShiftTradeResponse(ShiftTradeBase):
    id: int
    author: dict  # User info
    original_shift: dict  # Schedule info
    preferred_shift: Optional[dict] = None
    status: TradeStatus
    responses: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class ShiftTradeResponseBase(BaseModel):
    content: Optional[str] = None
    offered_shift_id: int


class ShiftTradeResponseCreate(BaseModel):
    offered_shift_id: int
    content: Optional[str] = None


class ShiftTradeResponseDetail(BaseModel):
    id: int
    trade_request_id: int
    respondent: dict
    offered_shift: dict
    content: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
