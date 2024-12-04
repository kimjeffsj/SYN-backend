from datetime import datetime, timedelta
from typing import List, Optional

from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .schemas import (
    ScheduleBulkCreateDto,
    ScheduleCreate,
    ScheduleSearchParams,
    ScheduleUpdate,
)


class RepeatPattern:
    """Helper class for handling schedule repeat patterns"""

    @staticmethod
    def parse(pattern: str) -> tuple[str, int, list[int], datetime]:
        """Parse repeat pattern string (type|interval|days|end_date)"""
        try:
            pattern_type, interval, days, end_date = pattern.split("|")
            return (
                pattern_type,
                int(interval),
                [int(d) for d in days.split(",")] if days else [],
                datetime.fromisoformat(end_date),
            )
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid repeat pattern format: {str(e)}")

    @staticmethod
    def get_next_date(
        current_date: datetime, pattern_type: str, interval: int, days: list[int]
    ) -> datetime:
        """Calculate next occurrence based on pattern"""
        if pattern_type == "daily":
            return current_date + timedelta(days=interval)

        elif pattern_type == "weekly":
            # If no specific days are specified, use the same day of week
            if not days:
                return current_date + timedelta(weeks=interval)

            # Find next available day
            current_day = current_date.weekday()
            next_days = [d for d in days if d > current_day]

            if next_days:
                days_ahead = next_days[0] - current_day
            else:
                days_ahead = (7 - current_day) + days[0] + (7 * (interval - 1))

            return current_date + timedelta(days=days_ahead)

        elif pattern_type == "monthly":
            # Add months by replacing month and year values
            year = current_date.year + ((current_date.month + interval - 1) // 12)
            month = ((current_date.month + interval - 1) % 12) + 1

            return current_date.replace(year=year, month=month)

        else:
            raise ValueError(f"Unsupported repeat pattern type: {pattern_type}")


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
        db: Session, search_params: Optional[ScheduleSearchParams] = None
    ) -> List[Schedule]:
        """Get all schedules with optional filtering"""
        query = db.query(Schedule)

        if search_params:
            if search_params.user_id:
                query = query.filter(Schedule.user_id == search_params.user_id)

            if search_params.start_date:
                query = query.filter(Schedule.start_time >= search_params.start_date)

            if search_params.end_date:
                query = query.filter(Schedule.end_time <= search_params.end_date)

            if search_params.shift_type:
                query = query.filter(Schedule.shift_type == search_params.shift_type)

            if search_params.status:
                query = query.filter(Schedule.status == search_params.status)

        return query.order_by(Schedule.start_time.desc()).all()

    @staticmethod
    def create_schedule(
        db: Session, schedule_data: ScheduleCreate, created_by: int
    ) -> Schedule:
        """Create a new schedule"""
        # Handle repeating schedule
        if schedule_data.is_repeating and schedule_data.repeat_pattern:
            return ScheduleService._create_repeating_schedule(
                db, schedule_data, created_by
            )

        # Single schedule creation
        if schedule_data.start_time >= schedule_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )

        if ScheduleService._check_schedule_conflict(
            db, schedule_data.user_id, schedule_data.start_time, schedule_data.end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule conflicts with existing schedule",
            )

        try:
            db_schedule = Schedule(
                **schedule_data.model_dump(),
                created_by=created_by,
                status=ScheduleStatus.PENDING,
            )
            db.add(db_schedule)
            db.commit()
            db.refresh(db_schedule)
            return db_schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def bulk_create_schedules(
        db: Session, schedules_data: ScheduleBulkCreateDto, created_by: int
    ) -> List[Schedule]:
        """Create multiple schedules at once"""
        created_schedules = []

        try:
            for schedule_data in schedules_data.schedules:
                # Handle repeating schedules within bulk creation
                if schedule_data.is_repeating and schedule_data.repeat_pattern:
                    repeat_schedule = ScheduleService._create_repeating_schedule(
                        db, schedule_data, created_by
                    )
                    created_schedules.append(repeat_schedule)
                    continue

                if ScheduleService._check_schedule_conflict(
                    db,
                    schedule_data.user_id,
                    schedule_data.start_time,
                    schedule_data.end_time,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Schedule conflict found for user {schedule_data.user_id}",
                    )

                db_schedule = Schedule(
                    **schedule_data.model_dump(),
                    created_by=created_by,
                    status=ScheduleStatus.PENDING,
                )
                db.add(db_schedule)
                created_schedules.append(db_schedule)

            db.commit()
            for schedule in created_schedules:
                db.refresh(schedule)

            return created_schedules

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    def update_schedule(
        db: Session, schedule_id: int, schedule_update: ScheduleUpdate
    ) -> Schedule:
        """Update schedule details"""
        schedule = ScheduleService.get_schedule(db, schedule_id)

        update_data = schedule_update.model_dump(exclude_unset=True)

        # If updating times, check for conflicts
        if "start_time" in update_data or "end_time" in update_data:
            start_time = update_data.get("start_time", schedule.start_time)
            end_time = update_data.get("end_time", schedule.end_time)

            if start_time >= end_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="End time must be after start time",
                )

            if ScheduleService._check_schedule_conflict(
                db, schedule.user_id, start_time, end_time, schedule_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule conflicts with existing schedule",
                )

        try:
            for key, value in update_data.items():
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
    def _create_repeating_schedule(
        db: Session, schedule_data: ScheduleCreate, created_by: int
    ) -> Schedule:
        """Create a schedule with repeating pattern"""
        try:
            # Parse repeat pattern
            pattern_type, interval, days, end_date = RepeatPattern.parse(
                schedule_data.repeat_pattern
            )

            # Create parent schedule
            parent_schedule = Schedule(
                **schedule_data.model_dump(),
                created_by=created_by,
                status=ScheduleStatus.PENDING,
                is_repeating=True,
            )
            db.add(parent_schedule)
            db.flush()

            # Create child schedules
            current_date = schedule_data.start_time
            duration = schedule_data.end_time - schedule_data.start_time
            child_schedules = []

            while current_date <= end_date:
                if not ScheduleService._check_schedule_conflict(
                    db, schedule_data.user_id, current_date, current_date + duration
                ):
                    child_schedule = Schedule(
                        user_id=schedule_data.user_id,
                        start_time=current_date,
                        end_time=current_date + duration,
                        shift_type=schedule_data.shift_type,
                        description=schedule_data.description,
                        status=ScheduleStatus.PENDING,
                        is_repeating=True,
                        parent_schedule_id=parent_schedule.id,
                        created_by=created_by,
                    )
                    child_schedules.append(child_schedule)

                current_date = RepeatPattern.get_next_date(
                    current_date, pattern_type, interval, days
                )

            db.add_all(child_schedules)
            db.commit()
            db.refresh(parent_schedule)
            return parent_schedule

        except ValueError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
