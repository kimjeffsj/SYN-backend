from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.features.employee_management.schemas import (
    EmployeeCreate,
    EmployeeDetailResponse,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.features.employee_management.service import EmployeeManagementService
from app.models.user import User
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(tags=["Employee Management"])


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    return await EmployeeManagementService.create_employee(db, data)


@router.get("/", response_model=list[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    return await EmployeeManagementService.get_employees(db, skip, limit, search)


@router.get("/{employee_id}", response_model=EmployeeDetailResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    return await EmployeeManagementService.get_employee(db, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    return await EmployeeManagementService.update_employee(db, employee_id, data)
