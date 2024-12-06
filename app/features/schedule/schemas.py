from datetime import datetime
from typing import List, Optional

from app.models import ScheduleStatus, ShiftType
from app.models.schedule_enums import RepeatFrequency
from pydantic import BaseModel, Field


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


class RepeatingPattern(BaseModel):
    """Schema for repeating schedule"""

    type: RepeatFrequency
    interval: int = Field(..., gt=0)
    days: Optional[List[int]] = Field(
        None, description="Days of week (0-6) for weekly pattern"
    )
    end_date: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "type": "weekly",
                "interval": 1,
                "days": [0, 2, 4],  # Mon, Wed, Fri
                "end_date": "2024-12-31T00:00:00Z",
            }
        }


class BulkScheduleCreate(BaseModel):
    """Creating multiple schedules"""

    schedules: List[ScheduleCreate] = Field(..., min_items=1)


class Config:
    json_schema_extra = {
        "example": {
            "schedules": [
                {
                    "start_time": "2024-12-05T22:40:16.268Z",
                    "end_time": "2024-12-05T22:40:16.268Z",
                    "shift_type": "morning",
                    "description": "string",
                    "is_repeating": False,
                    "repeat_pattern": None,
                    "user_id": 1,
                },
                {
                    "start_time": "2024-12-05T22:40:16.268Z",
                    "end_time": "2024-12-05T22:40:16.268Z",
                    "shift_type": "evening",
                    "description": "string",
                    "is_repeating": False,
                    "repeat_pattern": None,
                    "user_id": 2,
                },
            ]
        }
    }


class RepeatingScheduleCreate(BaseModel):
    """Schema for creating repeating schedule"""

    base_schedule: ScheduleCreate
    pattern: RepeatingPattern

    class Config:
        json_schema_extra = {
            "example": {
                "base_schedule": {
                    "user_id": 1,
                    "start_time": "2024-12-01T09:00:00Z",
                    "end_time": "2024-12-01T17:00:00Z",
                    "shift_type": ShiftType.MORNING.value,
                    "description": "Regular morning shift",
                },
                "pattern": {
                    "type": RepeatFrequency.WEEKLY.value,
                    "interval": 1,
                    "days": [0, 2, 4],
                    "end_date": "2024-12-31T00:00:00Z",
                },
            }
        }
