from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmployeeDashboardBase(BaseModel):
    pass


class EmployeeDashboardResponse(BaseModel):
    employee: dict
    today_schedule: Optional[dict] = None
    weekly_schedule: list = []
    announcement: list = []

    model_config = ConfigDict(from_attributes=True)
