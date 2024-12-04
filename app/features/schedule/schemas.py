from datetime import datetime
from typing import List, Optional

from app.models import ScheduleStatus, ShiftType
from pydantic import BaseModel, Field, field_validator


class ScheduleBase(BaseModel):
    """Base Schedule schema containing common attributes"""

    start_time: datetime
    end_time: datetime
    shift_type: ShiftType
    description: Optional[str] = None
    is_repeating: bool = False
    repeat_pattern: Optional[str] = None

    @field_validator("end_time")
    def validate_end_time(cls, v: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and v <= start_time:
            raise ValueError("End time must be after start time")
        return v

    @field_validator("start_time", "end_time")
    def validate_timezone(cls, v: datetime):
        if v.tzinfo is None:
            raise ValueError("Datetime must include timezone information")
        return v


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule"""

    user_id: int


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule"""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    shift_type: Optional[ShiftType] = None
    status: Optional[ScheduleStatus] = None
    description: Optional[str] = None
    is_repeating: Optional[bool] = None
    repeat_pattern: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    """Schema for schedule response"""

    id: int
    user_id: int
    status: ScheduleStatus
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleSearchParams(BaseModel):
    """Schema for schedule search parameters"""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    shift_type: Optional[ShiftType] = None
    status: Optional[ScheduleStatus] = None


class ScheduleBulkCreateDto(BaseModel):
    """DTO for creating multiple schedules at once"""

    schedules: List[ScheduleCreate] = Field(..., min_items=1)
