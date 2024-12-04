from typing import Optional

from pydantic import BaseModel


class EmployeeDashboardBase(BaseModel):
    pass


class EmployeeDashboardResponse(BaseModel):
    employee: dict
    today_schedule: Optional[dict] = None
    weekly_schedule: list = []
    announcement: list = []

    class Config:
        from_attributes = True
