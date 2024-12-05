from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_admin_user
from backend.app.features.schedule.bulk_service import BulkScheduleService
from backend.app.features.schedule.schemas import (
    BulkScheduleCreate,
    RepeatingScheduleCreate,
)
from backend.app.models.user import User

router = APIRouter()


@router.post("/bulk")
async def create_bulk_schedules(
    schedules: BulkScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create multiple schedules at once"""
    return await BulkScheduleService.create_bulk_schedules(
        db, schedules.schedules, current_user.id
    )


@router.post("/repeating")
async def create_repeating_schedule(
    schedule: RepeatingScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create Repeating schedule"""
    return await BulkScheduleService.create_repeating_schedules(
        db, schedule.base_schedule, schedule.pattern, current_user.id
    )
