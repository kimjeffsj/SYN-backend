import logging
from typing import List, Optional

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.core.security import get_current_admin_user
from app.features.employee_management.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeDetailResponse,
    EmployeeResponse,
    EmployeeUpdate,
    PositionCreate,
    PositionResponse,
)
from app.features.employee_management.service import EmployeeManagementService
from app.models.user import User
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter(tags=["Employee Management"])

department_router = APIRouter(tags=["Employee Management/Departments"])

position_router = APIRouter(tags=["Employee Management/Positions"])


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


# Department routes
@department_router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get all departments"""
    logger.info(f"Get departments request from user: {current_user.id}")
    try:
        departments = await EmployeeManagementService.get_departments(db)
        logger.info(f"Found {len(departments)} departments")
        return departments
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        raise


@department_router.post("/", response_model=DepartmentResponse)
async def add_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Add new department"""
    return await EmployeeManagementService.add_department(db, data)


@department_router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    """Delete department"""
    await EmployeeManagementService.delete_department(db, department_id)
    return {"message": "Department deleted successfully"}


# Position routes
@position_router.get("/", response_model=List[PositionResponse])
async def get_positions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    """Get all positions"""
    return await EmployeeManagementService.get_positions(db)


@position_router.post("/", response_model=PositionResponse)
async def add_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    """Add new position"""
    return await EmployeeManagementService.add_position(db, data)


@position_router.delete("/{position_id}")
async def delete_position(
    position_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    """Delete position"""
    await EmployeeManagementService.delete_position(db, position_id)
    return {"message": "Position deleted successfully"}
