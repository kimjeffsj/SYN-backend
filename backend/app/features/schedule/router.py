from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.features.auth.models import User
from app.features.schedule.schemas import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.features.schedule.service import ScheduleService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create new schedule"""
    # Check authorization
    if current_user.role != "admin" and schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create schedule for other users",
        )

    return ScheduleService.create_schedule(db, schedule, current_user.id)


@router.get("/my-schedules", response_model=List[ScheduleResponse])
async def get_my_schedules(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get current user's schedules"""
    return ScheduleService.get_user_schedules(db, current_user.id)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get specific schedule"""
    schedule = ScheduleService.get_schedule(db, schedule_id)

    if current_user.role != "admin" and schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this schedule",
        )

    return schedule
