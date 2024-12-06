from datetime import datetime

from app.models.notification import Notification
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from app.models.user import User
from sqlalchemy import and_
from sqlalchemy.orm import Session


class AdminDashboardService:
    @staticmethod
    async def get_dashboard_stats(db: Session):
        """Get overall dashboard stats"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0)
        today_end = now.replace(hour=23, minute=59, second=59)

        # Employees stats
        total_employees = db.query(User).filter(User.role == "employee").count()
        active_employees = (
            db.query(User)
            .filter(
                User.role == "employee",
                User.is_active == True,
                User.is_on_leave == False,
            )
            .count()
        )
        on_leave = (
            db.query(User)
            .filter(User.role == "employee", User.is_on_leave == True)
            .count()
        )

        # Schedule stats
        today_schedules = (
            db.query(Schedule)
            .filter(Schedule.start_time.between(today_start, today_end))
            .count()
        )

        pending_requests = (
            db.query(Schedule).filter(Schedule.status == ScheduleStatus.PENDING).count()
        )

        # Schedule conflicts
        conflicts = (
            db.query(Schedule)
            .filter(
                Schedule.status != ScheduleStatus.CANCELLED, Schedule.start_time >= now
            )
            .all()
        )

        conflict_count = 0
        for schedule in conflicts:
            overlapping = (
                db.query(Schedule)
                .filter(
                    Schedule.id != schedule.id,
                    Schedule.user_id == schedule.user_id,
                    Schedule.status != ScheduleStatus.CANCELLED,
                    and_(
                        Schedule.start_time < schedule.end_time,
                        Schedule.end_time > schedule.start_time,
                    ),
                )
                .first()
            )
            if overlapping:
                conflict_count += 1

        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "onLeave": on_leave,
                "pendingApproval": pending_requests,
            },
            "schedules": {
                "today": today_schedules,
                "pending": pending_requests,
                "conflicts": conflict_count,
            },
        }

    @staticmethod
    async def get_recent_updates(db: Session, limit: int = 10):
        """Get recent system updates and activities"""

        # Combine different types of activities
        activities = []

        # Recent schedule changes
        recent_schedules = (
            db.query(Schedule).order_by(Schedule.updated_at.desc()).limit(limit).all()
        )

        for schedule in recent_schedules:
            if schedule.updated_at:
                activities.append(
                    {
                        "id": schedule.id,
                        "type": "SCHEDULE_CHANGE",
                        "title": f"Schedule {schedule.status.lower()}",
                        "description": f"Schedule for {schedule.user.full_name}",
                        "user": schedule.user.full_name,
                        "timestamp": schedule.updated_at,
                        "status": schedule.status,
                    }
                )

        # Recent notifications
        recent_notifications = (
            db.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )

        for notification in recent_notifications:
            if notification.created_at:
                activities.append(
                    {
                        "id": notification.id,
                        "type": notification.type,
                        "title": "New Notification",
                        "description": notification.message,
                        "user": notification.user.full_name,
                        "timestamp": notification.created_at,
                        "status": "completed" if notification.is_read else "pending",
                    }
                )

        # Sort combined activities by timestamp
        if activities:
            activities.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)

        return activities

    @staticmethod
    async def get_employee_overview(db: Session):
        """Get employees overview with current stats"""
        employees = db.query(User).filter(User.role == "employee").all()

        return [
            {
                "id": emp.id,
                "name": emp.full_name,
                "position": emp.position,
                "department": emp.department,
                "status": "onLeave" if emp.is_on_leave else "active",
                "currentShift": await AdminDashboardService._get_current_shift(
                    db, emp.id
                ),
            }
            for emp in employees
        ]

    @staticmethod
    async def _get_current_shift(db: Session, user_id: int) -> str:
        """Helper to get user's current shift"""
        now = datetime.now()
        current_shift = (
            db.query(Schedule).filter(
                Schedule.user_id == user_id,
                Schedule.start_time <= now,
                Schedule.end_time >= now,
                Schedule.status == ScheduleStatus.CONFIRMED,
            )
        ).first()

        if current_shift:
            return f"{current_shift.start_time.strftime('%H:%M')}-{current_shift.end_time.strftime('%H:%M')}"
        return None

    @staticmethod
    async def get_announcements(db: Session):
        # TODO: Implement announcements
        return []
