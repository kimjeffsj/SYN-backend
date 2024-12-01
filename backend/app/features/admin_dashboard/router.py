from app.core.database import get_db
from app.core.security import get_current_active_user
from app.features.admin_dashboard.schemas import DashboardResponse
from app.features.admin_dashboard.service import AdminDashboardService
from app.features.auth.models import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get admin dashboard data"""
    try:
        stats = await AdminDashboardService.get_stats(db)
        recent_updates = await AdminDashboardService.get_recent_updates(db)
        employees = await AdminDashboardService.get_employees(db)
        announcements = await AdminDashboardService.get_announcements(db)

        return {
            "stats": stats,
            "recent_updates": recent_updates,
            "employees": employees,
            "announcements": announcements,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
