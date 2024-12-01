from datetime import datetime, timedelta

from app.models.schedule import Schedule
from app.models.user import User
from sqlalchemy.orm import Session


class EmployeeDashboardService:
    @staticmethod
    async def get_dashboard_data(db: Session, user: User):
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Get Today's schedule
        today_schedule = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user.id,
                Schedule.start_time >= today.replace(hour=0, minute=0, second=0),
                Schedule.start_time < today.replace(hour=23, minute=59, second=59),
            )
            .first()
        )

        # Get Weekly schedule
        weekly_schedule = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user.id,
                Schedule.start_time >= week_start,
                Schedule.start_time <= week_end,
            )
            .all()
        )

        # Get Recent announcements
        # TODO: will add announcement model later
        announcements = [
            {
                "id": 1,
                "title": "November News Letter",
                "date": "2024-11-15",
                "is_new": True,
            },
            {
                "id": 2,
                "title": "November's Shifts",
                "date": "2024-11-1",
                "is_new": True,
            },
            {
                "id": 3,
                "title": "October News Letter",
                "date": "2024-10-15",
                "is_new": False,
            },
            {
                "id": 4,
                "title": "October's Shifts",
                "date": "2024-10-1",
                "is_new": False,
            },
        ]

        return {
            "employee": {
                "id": user.id,
                "name": user.full_name,
                # TODO: actual position and department needs to be added
                "position": "employee",
                "department": "Sales",
            },
            "today_schedule": today_schedule,
            "weekly_schedule": weekly_schedule,
            "announcements": announcements,
        }
