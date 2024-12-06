from typing import List

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .schemas import ScheduleResponse
from .service import ScheduleService

router = APIRouter(tags=["Employee"])


@router.get("/my-schedules", response_model=List[ScheduleResponse])
async def get_my_schedules(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's schedules"""
    return ScheduleService.get_user_schedules(db, current_user.id)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get specific schedule"""
    schedule = ScheduleService.get_schedule(db, schedule_id)
    if current_user.id != schedule.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this schedule",
        )
    return schedule
