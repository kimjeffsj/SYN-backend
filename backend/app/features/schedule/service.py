from datetime import datetime, timedelta
from typing import List, Optional

from app.features.schedule.models import Schedule, ScheduleStatus
from app.features.schedule.schemas import ScheduleCreate
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


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
    def create_schedule(
        db: Session, schedule: ScheduleCreate, created_by: int
    ) -> Schedule:
        """Create a new schedule"""
        # Check timezone info
        if schedule.start_time.tzinfo is None or schedule.end_time.tzinfo is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timezone information is required",
            )

        # Process repeating schedule
        if schedule.is_repeating and schedule.repeat_pattern:
            return ScheduleService._create_repeating_schedule(db, schedule, created_by)

        # Check schedule conflicts
        if ScheduleService._check_schedule_conflict(
            db, schedule.user_id, schedule.start_time, schedule.end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule conflicts with existing schedule",
            )

        try:
            db_schedule = Schedule(
                **schedule.model_dump(),
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
    def _create_repeating_schedule(
        db: Session, schedule: ScheduleCreate, created_by: int
    ) -> Schedule:
        """Create repeating schedule with its occurrences"""
        try:
            # Parse repeat pattern
            pattern_type, interval, days, end_date = RepeatPattern.parse(
                schedule.repeat_pattern
            )

            # Create parent schedule
            parent_schedule = Schedule(
                **schedule.model_dump(),
                created_by=created_by,
                status=ScheduleStatus.PENDING,
                is_repeating=True,
            )
            db.add(parent_schedule)
            db.flush()  # Get parent_schedule.id without committing

            # Create child schedules
            current_date = schedule.start_time
            duration = schedule.end_time - schedule.start_time
            child_schedules = []

            while current_date <= end_date:
                # Skip if there's a conflict
                if not ScheduleService._check_schedule_conflict(
                    db, schedule.user_id, current_date, current_date + duration
                ):
                    child_schedule = Schedule(
                        user_id=schedule.user_id,
                        start_time=current_date,
                        end_time=current_date + duration,
                        shift_type=schedule.shift_type,
                        description=schedule.description,
                        status=ScheduleStatus.PENDING,
                        is_repeating=True,
                        parent_schedule_id=parent_schedule.id,
                        created_by=created_by,
                    )
                    child_schedules.append(child_schedule)

                # Calculate next occurrence
                current_date = RepeatPattern.get_next_date(
                    current_date, pattern_type, interval, days
                )

            db.add_all(child_schedules)
            db.commit()
            db.refresh(parent_schedule)
            return parent_schedule

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        schedule_id: Optional[int] = None,
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

        if schedule_id:
            query = query.filter(Schedule.id != schedule_id)

        return query.first() is not None

    @staticmethod
    def get_schedule(db: Session, schedule_id: int) -> Schedule:
        """Get schedule by ID"""
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
            )
        return schedule

    @staticmethod
    def get_user_schedules(db: Session, user_id: int) -> List[Schedule]:
        """Get all schedules for a specific user"""
        return db.query(Schedule).filter(Schedule.user_id == user_id).all()
