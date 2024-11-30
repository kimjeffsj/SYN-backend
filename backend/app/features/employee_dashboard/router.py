from app.core.database import get_db
from app.core.security import get_current_active_user
from app.features.auth.models import User
from app.features.employee_dashboard.models import EmployeeDashboardResponse
from app.features.employee_dashboard.service import EmployeeDashboardService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    return await EmployeeDashboardService.get_dashboard_data(db, current_user)
