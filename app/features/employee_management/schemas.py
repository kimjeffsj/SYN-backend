from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class EmployeeBase(BaseModel):
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    comment: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    email: EmailStr
    password: str


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None
    comment: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: int
    email: str
    full_name: str
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeDetailResponse(EmployeeResponse):
    is_on_leave: bool
    leave_balance: int
    last_active_at: Optional[datetime]
