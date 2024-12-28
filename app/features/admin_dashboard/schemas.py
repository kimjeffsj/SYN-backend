from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    employees: dict
    requests: dict


class RecentUpdate(BaseModel):
    id: int
    type: str
    title: str
    description: str
    timestamp: datetime
    status: str


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_updates: list[RecentUpdate]
    employees: list[dict]
    announcements: list[dict]

    model_config = ConfigDict(from_attributes=True)


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


class EmployeeOverviewResponse(BaseModel):
    id: int
    name: str
    position: Optional[str]
    department: Optional[str]
    status: str
    currentShift: Optional[str]

    model_config = ConfigDict(from_attributes=True)
