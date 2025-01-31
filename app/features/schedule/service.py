from datetime import datetime, timedelta
from typing import List, Optional

from app.core.events import Event, event_bus
from app.features.notifications.events.types import NotificationEventType
from app.features.schedule.bulk_service import BulkScheduleService
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus, ShiftType
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload


class ScheduleService:
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
        schedules = (
            db.query(Schedule)
            .options(joinedload(Schedule.user))
            .filter(Schedule.user_id == user_id)
            .order_by(Schedule.start_time.desc())
            .all()
        )

        return [
            BulkScheduleService._format_schedule(schedule) for schedule in schedules
        ]

    @staticmethod
    def get_all_schedules(
        db: Session,
        search_params: Optional[dict] = None,
        admin_id: int = None,
    ) -> List[Schedule]:
        """Get all schedules with optional filtering"""
        query = (
            db.query(Schedule)
            .join(User, Schedule.user_id == User.id)
            .options(joinedload(Schedule.user))
        )

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

        schedules = query.order_by(Schedule.start_time.desc()).all()

        return [ScheduleService._format_schedule(schedule) for schedule in schedules]

    @staticmethod
    async def create_schedule(
        db: Session, schedule_data: dict, created_by: int
    ) -> Schedule:
        """Create a single schedule"""

        if schedule_data["start_time"] >= schedule_data["end_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End time must be after start time",
            )

        has_conflict = ScheduleService._check_schedule_conflict(
            db,
            user_id=schedule_data["user_id"],
            start_time=schedule_data["start_time"],
            end_time=schedule_data["end_time"],
        )

        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule conflicts with existing schedule",
            )

        try:
            schedule = Schedule(
                **schedule_data, created_by=created_by, status=ScheduleStatus.CONFIRMED
            )

            db.add(schedule)
            db.commit()
            db.refresh(schedule)

            schedule = (
                db.query(Schedule)
                .options(joinedload(Schedule.user))
                .filter(Schedule.id == schedule.id)
                .first()
            )

            # Create notification for the employee

            formatted_schedule = ScheduleService._format_schedule(schedule)

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

            return formatted_schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def update_schedule(
        db: Session, schedule_id: int, schedule_data: dict
    ) -> Schedule:
        """Update schedule details"""
        schedule = ScheduleService.get_schedule(db, schedule_id)

        # Store original data for notification
        original_data = {
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "shift_type": schedule.shift_type.value,
            "status": schedule.status.value,
        }

        try:
            for key, value in schedule_data.items():
                setattr(schedule, key, value)

            db.commit()
            db.refresh(schedule)

            # Create notification for schedule update
            notification = Notification(
                user_id=schedule.user_id,
                type=NotificationType.SCHEDULE_CHANGE,
                title="Schedule Updated",
                message=f"Your schedule for {schedule.start_time.strftime('%Y-%m-%d')} has been updated",
                priority=NotificationPriority.HIGH,
                data={
                    "schedule_id": schedule.id,
                    "original": original_data,
                    "updated": {
                        "start_time": schedule.start_time.isoformat(),
                        "end_time": schedule.end_time.isoformat(),
                        "shift_type": schedule.shift_type.value,
                        "status": schedule.status.value,
                    },
                    "changes": schedule_data,
                },
            )
            db.add(notification)
            db.commit()

            # Event for real-time notification
            await event_bus.publish(
                Event(
                    type=NotificationEventType.SCHEDULE_UPDATED,
                    data={
                        "schedule": ScheduleService._format_schedule(schedule),
                        "notification": notification.to_dict(),
                    },
                )
            )

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
            notification = Notification(
                user_id=schedule.user_id,
                type=NotificationType.SCHEDULE_CHANGE,
                title="Schedule Deleted",
                message=f"Schedule for {schedule.start_time.strftime('%Y-%m-%d')} has been deleted",
                priority=NotificationPriority.HIGH,
                data={
                    "schedule_id": schedule.id,
                    "date": schedule.start_time.strftime("%Y-%m-%d"),
                },
            )
            db.add(notification)

            db.delete(schedule)
            db.commit()

            return {"message": "Schedule deleted successfully"}

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def update_schedule_status(
        db: Session, schedule_id: int, new_status: str
    ) -> Schedule:
        """Update schedule status"""
        schedule = ScheduleService.get_schedule(db, schedule_id)
        old_status = schedule.status

        try:
            schedule.status = new_status

            notification = Notification(
                user_id=schedule.user_id,
                type=NotificationType.SCHEDULE_CHANGE,
                title="Schedule Status Updated",
                message=f"Your schedule status has been updated to {new_status}",
                priority=NotificationPriority.NORMAL,
                data={
                    "schedule_id": schedule.id,
                    "old_status": old_status.value,
                    "new_status": new_status,
                    "date": schedule.start_time.strftime("%Y-%m-%d"),
                },
            )
            db.add(notification)

            db.commit()
            db.refresh(schedule)

            # Event for real-time notification
            await event_bus.publish(
                Event(
                    type=NotificationEventType.SCHEDULE_UPDATED,
                    data={
                        "schedule": ScheduleService._format_schedule(schedule),
                        "notification": notification.to_dict(),
                    },
                )
            )

            return schedule

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def get_schedule_overview(
        db: Session, start_date: datetime, end_date: datetime, view_type: str = "week"
    ) -> dict:
        """Overview of schedules"""
        base_query = db.query(Schedule).filter(
            and_(
                Schedule.start_time >= start_date,
                Schedule.end_time <= end_date,
                Schedule.status != ScheduleStatus.CANCELLED,
            )
        )

        # Daily stats
        daily_stats = {}
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            # Get schedules for the day
            day_schedules = base_query.filter(
                and_(
                    Schedule.start_time >= current_date,
                    Schedule.end_time < next_date,
                )
            ).all()

            daily_stats[current_date.strftime("%Y-%m-%d")] = {
                "total_count": len(day_schedules),
                "shift_counts": {
                    "morning": sum(
                        1 for s in day_schedules if s.shift_type == ShiftType.MORNING
                    ),
                    "afternoon": sum(
                        1 for s in day_schedules if s.shift_type == ShiftType.AFTERNOON
                    ),
                    "evening": sum(
                        1 for s in day_schedules if s.shift_type == ShiftType.EVENING
                    ),
                },
                "status_counts": {
                    "confirmed": sum(
                        1 for s in day_schedules if s.status == ScheduleStatus.CONFIRMED
                    ),
                    "pending": sum(
                        1 for s in day_schedules if s.status == ScheduleStatus.PENDING
                    ),
                },
                "schedules": [
                    {
                        "id": schedule.id,
                        "user_id": schedule.user_id,
                        "user": {
                            "id": schedule.user.id,
                            "name": schedule.user.full_name,
                            "position": schedule.user.position,
                        },
                        "shift_type": schedule.shift_type.value,
                        "start_time": schedule.start_time.strftime("%H:%M"),
                        "end_time": schedule.end_time.strftime("%H:%M"),
                        "status": schedule.status.value,
                    }
                    for schedule in day_schedules
                ],
            }

            current_date = next_date

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "view_type": view_type,
            "daily_stats": daily_stats,
        }

    @staticmethod
    def _check_schedule_conflict(
        db: Session,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_schedule_id: Optional[int] = None,
    ) -> bool:
        """Check for schedule conflicts"""
        query = db.query(Schedule).filter(
            and_(
                Schedule.user_id == user_id,
                Schedule.status != ScheduleStatus.CANCELLED,
                Schedule.start_time < end_time,
                Schedule.end_time > start_time,
            )
        )

        if exclude_schedule_id:
            query = query.filter(Schedule.id != exclude_schedule_id)

        existing = query.first()

        if existing:
            print(
                f"""
            Conflict detected:
            New Schedule: {start_time} - {end_time}
            Existing Schedule: {existing.start_time} - {existing.end_time}
            """
            )

        return existing is not None
