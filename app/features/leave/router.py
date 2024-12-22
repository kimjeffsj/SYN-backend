from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin_user, get_current_user
from app.features.leave.schemas import (
    LeaveRequestCreate,
    LeaveRequestList,
    LeaveRequestResponse,
    LeaveRequestUpdate,
)
from app.features.leave.service import LeaveRequestService
from app.models.leave_request import LeaveStatus
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Leave Requests"])


@router.get("/", response_model=LeaveRequestList)
async def get_leave_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get all leave requests"""
    requests = LeaveRequestService.get_leave_requests(db, status=status)
    total = len(requests)
    pending = sum(1 for req in requests if req["status"] == LeaveStatus.PENDING)
    return {"items": requests, "total": total, "pending": pending}


@router.get("/my-requests", response_model=LeaveRequestList)
async def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's leave requests"""
    return LeaveRequestService.get_leave_requests(db, employee_id=current_user.id)


@router.get("/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific leave request details"""
    request = LeaveRequestService.get_leave_request(db, request_id)
    if current_user.role != "admin" and request.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request",
        )
    return request


@router.post("/", response_model=LeaveRequestResponse)
async def create_leave_request(
    request: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new leave request"""
    return await LeaveRequestService.create_leave_request(
        db, request.model_dump(), current_user.id
    )


from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_admin_user, get_current_user
from app.models.leave_request import LeaveStatus
from app.models.user import User
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .schemas import (
    LeaveRequestCreate,
    LeaveRequestList,
    LeaveRequestResponse,
    LeaveRequestUpdate,
)
from .service import LeaveRequestService

router = APIRouter(tags=["Leave Management"])


@router.get("/", response_model=LeaveRequestList)
async def get_leave_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get all leave requests (admin only)"""
    requests = LeaveRequestService.get_leave_requests(db, status=status)
    total = len(requests)
    pending = sum(1 for req in requests if req["status"] == LeaveStatus.PENDING)
    return {"items": requests, "total": total, "pending": pending}


@router.get("/my-requests", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's leave requests"""
    return LeaveRequestService.get_leave_requests(db, employee_id=current_user.id)


@router.get("/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific leave request details"""
    request = LeaveRequestService.get_leave_request(db, request_id)
    if current_user.role != "admin" and request.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request",
        )
    return request


@router.post("/", response_model=LeaveRequestResponse)
async def create_leave_request(
    request: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new leave request"""
    return await LeaveRequestService.create_leave_request(
        db, request.model_dump(), current_user.id
    )


@router.patch("/{request_id}", response_model=LeaveRequestResponse)
async def process_leave_request(
    request_id: int,
    request_update: LeaveRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Process (approve/reject) a leave request (admin only)"""
    return await LeaveRequestService.process_leave_request(
        db,
        request_id,
        current_user.id,
        request_update.status,
        request_update.comment,
    )


@router.delete("/{request_id}")
async def cancel_leave_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending leave request"""
    return await LeaveRequestService.cancel_leave_request(
        db, request_id, current_user.id
    )
