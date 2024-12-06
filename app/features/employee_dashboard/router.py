from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .schemas import EmployeeDashboardResponse
from .service import EmployeeDashboardService

router = APIRouter(tags=["Dashboard", "Employee"])


@router.get("/", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get employee dashboard data"""
    return await EmployeeDashboardService.get_dashboard_data(db, current_user.id)
