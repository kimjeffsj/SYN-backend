from datetime import datetime, timedelta

from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session


class EmployeeDashboardService:
    @staticmethod
    async def get_dashboard_data(db: Session, user_id: int):
        """Get employee's dashboard data"""
        user = db.query(User).get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get Today's schedule
        today = datetime.now()
        today_start = today.replace(hour=0, minute=0, second=0)
        today_end = today.replace(hour=23, minute=59, second=59)

        today_schedule = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user.id,
                Schedule.start_time.between(today_start, today_end),
            )
            .first()
        )

        # Get Weekly schedule
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        weekly_schedule = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.start_time.between(week_start, week_end),
            )
            .all()
        )

        # Calc stats
        total_hours = sum(
            (s.end_time - s.start_time).total_seconds() / 3600
            for s in db.query(Schedule)
            .filter(
                Schedule.user_id == user_id, Schedule.status == ScheduleStatus.COMPLETED
            )
            .all()
        )

        completed_shifts = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user_id, Schedule.status == ScheduleStatus.COMPLETED
            )
            .count()
        )

        upcoming_shifts = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.start_time > today,
                Schedule.status == ScheduleStatus.CONFIRMED,
            )
            .count()
        )

        return {
            "employee": {
                "id": user.id,
                "name": user.full_name,
                "position": user.position,
                "department": user.department,
            },
            "stats": {
                "totalHours": round(total_hours, 1),
                "completedShifts": completed_shifts,
                "upcomingShifts": upcoming_shifts,
                "leaveBalance": user.leave_balance,
            },
            "todaySchedule": today_schedule,
            "weeklySchedule": weekly_schedule,
        }
