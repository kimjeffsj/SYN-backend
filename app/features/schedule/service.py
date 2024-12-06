from datetime import datetime
from typing import List, Optional

from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .schemas import ScheduleCreate, ScheduleSearchParams


class ScheduleService:
    @staticmethod
    def get_schedule(db: Session, schedule_id: int) -> Schedule:
        """Get a specific schedule by ID"""
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )
        return schedule

    @staticmethod
    def get_user_schedules(db: Session, user_id: int) -> List[Schedule]:
        """Get all schedules for a specific user"""
        return (
            db.query(Schedule)
            .filter(Schedule.user_id == user_id)
            .order_by(Schedule.start_time.desc())
            .all()
        )

    @staticmethod
    def get_all_schedules(
        db: Session, search_params: Optional[dict] = None
    ) -> List[Schedule]:
        """Get all schedules with optional filtering"""
        query = db.query(Schedule)

        if search_params:
            if search_params.get("user_id"):
                query = query.filter(Schedule.user_id == search_params["user_id"])

            if search_params.get("start_date"):
                query = query.filter(Schedule.start_time >= search_params["start_date"])

            if search_params.get("end_date"):
                query = query.filter(Schedule.end_time <= search_params["end_date"])

            if search_params.get("shift_type"):
                query = query.filter(Schedule.shift_type == search_params["shift_type"])

            if search_params.get("status"):
                query = query.filter(Schedule.status == search_params["status"])

        return query.order_by(Schedule.start_time.desc()).all()

    @staticmethod
    def create_schedule(db: Session, schedule_data: dict, created_by: int) -> Schedule:
        """Create a single schedule"""
        if schedule_data["start_time"] >= schedule_data["end_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )

        try:
            schedule = Schedule(
                **schedule_data, created_by=created_by, status=ScheduleStatus.PENDING
            )
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
            return schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def update_schedule(db: Session, schedule_id: int, schedule_data: dict) -> Schedule:
        """Update schedule details"""
        schedule = ScheduleService.get_schedule(db, schedule_id)

        try:
            for key, value in schedule_data.items():
                setattr(schedule, key, value)

            db.commit()
            db.refresh(schedule)
            return schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> dict:
        """Delete a schedule"""
        schedule = ScheduleService.get_schedule(db, schedule_id)

        try:
            db.delete(schedule)
            db.commit()
            return {"message": "Schedule deleted successfully"}

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def update_schedule_status(
        db: Session, schedule_id: int, new_status: str
    ) -> Schedule:
        """Update schedule status"""
        schedule = ScheduleService.get_schedule(db, schedule_id)

        try:
            schedule.status = new_status
            db.commit()
            db.refresh(schedule)
            return schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def _check_schedule_conflict(
        db: Session,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_schedule_id: Optional[int] = None,
    ) -> bool:
        """Check if schedule conflicts with existing schedules"""
        query = db.query(Schedule).filter(
            and_(
                Schedule.user_id == user_id,
                Schedule.status != ScheduleStatus.CANCELLED,
                or_(
                    and_(
                        Schedule.start_time <= start_time,
                        Schedule.end_time > start_time,
                    ),
                    and_(Schedule.start_time < end_time, Schedule.end_time >= end_time),
                    and_(
                        Schedule.start_time >= start_time, Schedule.end_time <= end_time
                    ),
                ),
            )
        )

        if exclude_schedule_id:
            query = query.filter(Schedule.id != exclude_schedule_id)

        return query.first() is not None
