from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models import User

from .schemas import (
    DashboardStatsDetailResponse,
    EmployeeOverviewResponse,
    RecentUpdate,
)
from .service import AdminDashboardService

router = APIRouter(tags=["Dashboard", "Admin"])


@router.get("/", response_model=DashboardStatsDetailResponse)
async def get_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """Get admin dashboard main view"""
    return await AdminDashboardService.get_dashboard_stats(db)


@router.get("/stats", response_model=DashboardStatsDetailResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """Get detailed admin dashboard statistics"""
    return await AdminDashboardService.get_dashboard_stats(db)


@router.get("/updates", response_model=list[RecentUpdate])
async def get_recent_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    limit: int = 10,
):
    """Get recent system updates"""
    return await AdminDashboardService.get_recent_updates(db, limit)


@router.get("/employees", response_model=list[EmployeeOverviewResponse])
async def get_employee_overview(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)
):
    """Get detailed employee overview"""
    return await AdminDashboardService.get_employee_overview(db)
