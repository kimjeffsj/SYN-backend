from datetime import datetime
from typing import List, Optional

from app.models import ScheduleStatus, ShiftType
from app.models.schedule_enums import RepeatFrequency
from pydantic import BaseModel, ConfigDict, Field


class ScheduleBase(BaseModel):
    """Base Schedule schema containing common attributes"""

    start_time: datetime
    end_time: datetime
    shift_type: ShiftType
    description: Optional[str] = None
    is_repeating: bool = False
    repeat_frequency: Optional[RepeatFrequency] = None
    repeat_interval: Optional[int] = None
    repeat_days: Optional[str] = None
    repeat_end_date: Optional[datetime] = None


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule"""

    user_id: int


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule"""

    start_time: datetime
    end_time: datetime
    shift_type: ShiftType
    description: Optional[str] = None
    is_repeating: bool = False
    repeat_frequency: Optional[RepeatFrequency] = None
    repeat_interval: Optional[int] = None
    repeat_days: Optional[str] = None
    repeat_end_date: Optional[datetime] = None


class ScheduleResponse(ScheduleBase):
    """Schema for schedule response"""

    id: int
    user_id: int
    user: dict
    status: ScheduleStatus
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleSearchParams(BaseModel):
    """Schema for schedule search parameters"""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    shift_type: Optional[ShiftType] = None
    status: Optional[ScheduleStatus] = None


class RepeatingPattern(BaseModel):
    """Schema for repeating schedule"""

    type: RepeatFrequency
    interval: int = Field(..., gt=0)
    days: Optional[List[int]] = Field(
        None, description="Days of week (0-6) for weekly pattern"
    )
    end_date: datetime


class BulkScheduleCreate(BaseModel):
    """Creating multiple schedules"""

    schedules: List[ScheduleCreate] = Field(..., min_length=1)


class RepeatingScheduleCreate(BaseModel):
    """Schema for creating repeating schedule"""

    base_schedule: ScheduleCreate
    pattern: RepeatingPattern
