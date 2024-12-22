from datetime import datetime
from typing import Optional

from app.models.leave_request import LeaveStatus, LeaveType
from pydantic import BaseModel, field_validator


class LeaveRequestBase(BaseModel):
    """Base schema for leave request"""

    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    reason: str

    @field_validator("end_date")
    def validate_end_date(cls, v: datetime, values: dict) -> datetime:
        start_date = values.get("start_date")
        if start_date and v < start_date:
            raise ValueError("End Date must be greater than Start date")
        return v


class LeaveRequestCreate(LeaveRequestBase):
    """Schema for creating leave request"""

    pass


class LeaveRequestUpdate(LeaveRequestBase):
    """Schema for updating leave request"""

    status: LeaveStatus
    comment: Optional[str] = None


class AdminResponse(BaseModel):
    """Schema for admin"""

    admin_id: int
    admin_name: str
    comment: Optional[str]
    processed_at: datetime

    class Config:
        from_attributes = True


class LeaveRequestResponse(LeaveRequestBase):
    """Schema for leave request response"""

    id: int
    employee_id: int
    employee: dict
    status: LeaveStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    admin_response: Optional[AdminResponse] = None

    class Config:
        from_attributes = True


class LeaveRequestList(BaseModel):
    """Schema for list of leave requests"""

    items: list[LeaveRequestResponse]
    total: int
    pending: int

    class Config:
        from_attributes = True
