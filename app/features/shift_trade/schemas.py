from datetime import datetime
from typing import List, Optional

from app.models.shift_trade import ResponseStatus, TradeStatus, TradeType, UrgencyLevel
from pydantic import BaseModel, ConfigDict


class ShiftTradeBase(BaseModel):
    type: TradeType
    original_shift_id: int
    preferred_shift_id: Optional[int] = None
    reason: Optional[str] = None
    urgency: UrgencyLevel = UrgencyLevel.NORMAL


class ShiftTradeCreate(ShiftTradeBase):
    pass


class ScheduleInfo(BaseModel):
    id: int
    start_time: str
    end_time: str
    type: str

    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    id: int
    name: str
    position: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TradeResponseInfo(BaseModel):
    id: int
    respondent: UserInfo
    offered_shift: Optional[ScheduleInfo]
    content: Optional[str]
    status: ResponseStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShiftTradeResponse(ShiftTradeBase):
    id: int
    author_id: int
    status: TradeStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    author: UserInfo
    original_shift: ScheduleInfo
    preferred_shift: Optional[ScheduleInfo] = None
    responses: List[TradeResponseInfo] = []

    model_config = ConfigDict(from_attributes=True)


class TradeResponseCreate(BaseModel):
    offered_shift_id: int
    content: Optional[str] = None


class TradeResponseUpdate(BaseModel):
    status: ResponseStatus  # ACCEPTED or REJECTED
