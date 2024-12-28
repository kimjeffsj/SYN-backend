from datetime import datetime
from typing import Optional

from app.models.leave_request import LeaveStatus, LeaveType
from pydantic import BaseModel, ConfigDict, field_validator


class LeaveRequestBase(BaseModel):
    """Base schema for leave request"""

    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    reason: str

    @field_validator("end_date")
    def validate_end_date(cls, v: datetime, info):
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("End date must be after start date")
        return v

    @field_validator("start_date")
    def validate_start_date(cls, v: datetime):
        if v.date() < datetime.now().date():
            raise ValueError("Start date cannot be in the past")
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

    model_config = ConfigDict(from_attributes=True)


class RequestEmployee(BaseModel):
    id: int
    name: str
    position: str
    department: str


class LeaveRequestResponse(LeaveRequestBase):
    """Schema for leave request response"""

    id: int
    employee_id: int
    employee: RequestEmployee
    status: LeaveStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    admin_response: Optional[AdminResponse] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestList(BaseModel):
    """Schema for list of leave requests"""

    items: list[LeaveRequestResponse]
    total: int
    pending: int

    model_config = ConfigDict(from_attributes=True)
