from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EmployeeInfo(BaseModel):
    id: int
    name: str
    position: str
    department: str


class ScheduleItem(BaseModel):
    id: int
    date: datetime
    shift_type: str
    start_time: str
    end_time: str
    status: str


class Announcement(BaseModel):
    id: int
    title: str
    date: str
    is_new: bool


class EmployeeDashboardResponse(BaseModel):
    employee: EmployeeInfo
    today_schedule: Optional[ScheduleItem] = None
    weekly_schedule: list[ScheduleItem] = []
    announcements: list[Announcement] = []
