from datetime import datetime, timedelta
from typing import List, Optional, Union

from app.core.events import Event, event_bus
from app.features.notifications.events.types import NotificationEventType
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class BulkScheduleService:
    @staticmethod
    def _format_schedule(schedule: Schedule) -> dict:
        """Format schedule for API response"""
        return {
            "id": schedule.id,
            "user_id": schedule.user_id,
            "user": {
                "id": schedule.user.id,
                "name": schedule.user.full_name,
                "position": schedule.user.position,
                "department": schedule.user.department,
            },
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "shift_type": schedule.shift_type.value,
            "status": schedule.status.value,
            "description": schedule.description,
            "created_by": schedule.created_by,
            "created_at": (
                schedule.created_at.isoformat() if schedule.created_at else None
            ),
            "updated_at": (
                schedule.updated_at.isoformat() if schedule.updated_at else None
            ),
        }

    @staticmethod
    async def validate_schedules(db: Session, schedules: List[dict]) -> bool:
        """Validate bulk schedule creation request"""
        for schedule in schedules:
            # Check if user exist
            user = db.query(User).filter(User.id == schedule["user_id"]).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {schedule['user_id']} not found",
                )

            # Check schedule conflicts
            if await BulkScheduleService._check_schedule_conflict(
                db, schedule["user_id"], schedule["start_time"], schedule["end_time"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Schedule conflict found for user {schedule['user_id']}",
                )

        return True

    @staticmethod
    async def create_bulk_schedules(
        db: Session, schedules: List[dict], created_by: int
    ) -> List[Schedule]:
        """Create multiple schedules at once"""
        # Validate schedules first
        await BulkScheduleService.validate_schedules(db, schedules)

        created_schedules = []
        try:
            for schedule_data in schedules:
                schedule = Schedule(
                    **schedule_data,
                    created_by=created_by,
                    status=ScheduleStatus.CONFIRMED,
                )
                db.add(schedule)
                created_schedules.append(schedule)

            db.commit()
            for schedule in created_schedules:
                db.refresh(schedule)

                formatted_schedule = BulkScheduleService._format_schedule(schedule)
                notification = Notification(
                    user_id=schedule.user_id,
                    type=NotificationType.SCHEDULE_CHANGE,
                    title="New Schedule Assignment",
                    message=f"New schedule assigned for {schedule.start_time.strftime('%Y-%m-%d')}",
                    priority=NotificationPriority.NORMAL,
                    data=formatted_schedule,
                )

            db.add(notification)
            db.commit()

            # Event for real-time notification
            await event_bus.publish(
                Event(
                    type=NotificationEventType.SCHEDULE_UPDATED,
                    data={"schedule": formatted_schedule, "notification": notification},
                )
            )

            return [
                BulkScheduleService._format_schedule(schedule)
                for schedule in created_schedules
            ]

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def create_repeating_schedules(
        db: Session, base_schedule: dict, pattern: dict, created_by: int
    ) -> List[Schedule]:
        """Create repeating schedules"""
        schedules = []
        current_date = (
            base_schedule["start_time"]
            if isinstance(base_schedule["start_time"], datetime)
            else datetime.fromisoformat(base_schedule["start_time"])
        )
        end_date = (
            pattern["end_date"]
            if isinstance(pattern["end_date"], datetime)
            else datetime.fromisoformat(pattern["end_date"])
        )

        while current_date <= end_date:
            if (
                pattern["type"] == "weekly"
                and str(current_date.weekday()) not in pattern["days"]
            ):
                current_date += timedelta(days=1)
                continue

            schedule_data = {
                **base_schedule,
                "start_time": current_date.isoformat(),
                "end_time": (
                    current_date + timedelta(hours=int(base_schedule["duration"]))
                ).isoformat(),
            }

            try:
                if not await BulkScheduleService._check_schedule_conflict(
                    db,
                    base_schedule["user_id"],
                    schedule_data["start_time"],
                    schedule_data["end_time"],
                ):
                    schedules.append(schedule_data)
            except Exception:
                pass  # Skip conflicting schedules in repeating

            if pattern["type"] == "daily":
                current_date += timedelta(days=pattern["interval"])
            elif pattern["type"] == "weekly":
                current_date += timedelta(days=1)
            elif pattern["type"] == "monthly":
                current_date = current_date.replace(
                    month=current_date.month + pattern["interval"]
                )

        return await BulkScheduleService.create_bulk_schedules(
            db, schedules, created_by
        )

    @staticmethod
    async def _check_schedule_conflict(
        db: Session,
        user_id: int,
        start_time: Union[str, datetime],
        end_time: Union[str, datetime],
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Check for schedule conflicts"""
        start = (
            start_time
            if isinstance(start_time, datetime)
            else datetime.fromisoformat(start_time)
        )
        end = (
            end_time
            if isinstance(end_time, datetime)
            else datetime.fromisoformat(end_time)
        )

        query = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.status != ScheduleStatus.CANCELLED,
            Schedule.start_time < end,
            Schedule.end_time > start,
        )

        if exclude_id:
            query = query.filter(Schedule.id != exclude_id)

        return query.first() is not None
