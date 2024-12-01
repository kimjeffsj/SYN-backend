from app.features.auth.models import User
from sqlalchemy.orm import Session


class AdminDashboardService:
    @staticmethod
    async def get_stats(db: Session):
        total_employees = db.query(User).filter(User.role == "employee").count()
        active_employees = (
            db.query(User)
            .filter(User.role == "employee", User.is_active == True)
            .count()
        )

        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "onLeave": 0,  # TODO: Implement leave tracking
                "pendingApproval": 0,  # TODO: Implement approval tracking
            },
            "requests": {"timeOff": 0, "shiftTrade": 0, "total": 0},
        }

    @staticmethod
    async def get_recent_updates(db: Session):
        # TODO: Implement real updates tracking
        return []

    @staticmethod
    async def get_employees(db: Session):
        employees = db.query(User).filter(User.role == "employee").all()
        return [
            {
                "id": emp.id,
                "name": emp.full_name,
                "position": "Staff",  # TODO: Add position field to User model
                "department": "Main",  # TODO: Add department field to User model
                "status": "active" if emp.is_active else "inactive",
            }
            for emp in employees
        ]

    @staticmethod
    async def get_announcements(db: Session):
        # TODO: Implement announcements
        return []
