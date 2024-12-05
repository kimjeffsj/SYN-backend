from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardStatsEmployee(BaseModel):
    total: int
    active: int
    onLeave: int
    pendingApproval: int


class DashboardStatsSchedule(BaseModel):
    today: int
    pending: int
    conflicts: int


class DashboardStatsDetailResponse(BaseModel):
    employees: DashboardStatsEmployee
    schedules: DashboardStatsSchedule


class RecentUpdateResponse(BaseModel):
    id: str
    type: str
    user: str
    action: str
    timestamp: datetime
    status: str


class EmployeeOverviewResponse(BaseModel):
    id: int
    name: str
    position: Optional[str]
    department: Optional[str]
    status: str
    currentShift: Optional[str]

    class Config:
        from_attributes = True
