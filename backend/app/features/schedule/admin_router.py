from typing import List

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.user import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .schemas import (
    ScheduleBulkCreateDto,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleSearchParams,
    ScheduleUpdate,
)
from .service import ScheduleService

router = APIRouter()


@router.get("/", response_model=List[ScheduleResponse])
async def get_all_schedules(
    db: Session = Depends(get_db), search_params: ScheduleSearchParams = Depends()
):
    """Get all schedules with optional filtering"""
    return ScheduleService.get_all_schedules(db, search_params)


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create a new schedule"""
    return ScheduleService.create_schedule(db, schedule, admin.id)


@router.post("/bulk", response_model=List[ScheduleResponse])
async def create_bulk_schedules(
    schedules_data: ScheduleBulkCreateDto,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create multiple schedules at once"""
    return ScheduleService.bulk_create_schedules(db, schedules_data, admin.id)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int, schedule_update: ScheduleUpdate, db: Session = Depends(get_db)
):
    """Update schedule details"""
    return ScheduleService.update_schedule(db, schedule_id, schedule_update)


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete a schedule"""
    return ScheduleService.delete_schedule(db, schedule_id)


@router.patch("/{schedule_id}/status")
async def update_schedule_status(
    schedule_id: int, status: str, db: Session = Depends(get_db)
):
    """Update schedule status"""
    return ScheduleService.update_schedule_status(db, schedule_id, status)
