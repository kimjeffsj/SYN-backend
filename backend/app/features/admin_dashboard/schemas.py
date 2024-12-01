from datetime import datetime

from pydantic import BaseModel


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

    class Config:
        from_attributes = True
