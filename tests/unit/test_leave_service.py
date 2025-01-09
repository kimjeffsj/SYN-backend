from datetime import datetime, timedelta

import pytest
from app.features.leave.service import LeaveRequestService
from app.models.leave_request import LeaveRequest, LeaveStatus, LeaveType
from fastapi import HTTPException


@pytest.fixture
def leave_request_data():
    """Basic leave request data"""
    start_date = datetime.now() + timedelta(days=1)
    return {
        "leave_type": LeaveType.VACATION,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=2),
        "reason": "Annual vacation",
    }


@pytest.fixture
def pending_leave_request(db_session, test_user):
    """Creates a pending leave request"""
    start_date = datetime.now() + timedelta(days=1)
    request = LeaveRequest(
        employee_id=test_user.id,
        leave_type=LeaveType.VACATION,
        start_date=start_date,
        end_date=start_date + timedelta(days=2),
        reason="Test vacation",
        status=LeaveStatus.PENDING,
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


@pytest.fixture
def approved_leave_request(db_session, test_user, test_admin):
    """Creates an approved leave request"""
    start_date = datetime.now() + timedelta(days=3)
    request = LeaveRequest(
        employee_id=test_user.id,
        leave_type=LeaveType.VACATION,
        start_date=start_date,
        end_date=start_date + timedelta(days=1),
        reason="Approved vacation",
        status=LeaveStatus.APPROVED,
        admin_id=test_admin.id,
        admin_comment="Approved",
        processed_at=datetime.now(),
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request


@pytest.mark.asyncio
async def test_create_leave_request(db_session, test_user, leave_request_data):
    """Test creating a new leave request"""
    result = await LeaveRequestService.create_leave_request(
        db_session, leave_request_data, test_user.id
    )

    assert result["leave_type"] == leave_request_data["leave_type"].value
    assert result["status"] == LeaveStatus.PENDING.value
    assert result["employee"]["id"] == test_user.id


@pytest.mark.asyncio
async def test_get_leave_request(db_session, test_user, pending_leave_request):
    """Test retrieving a specific leave request"""
    request = LeaveRequestService.get_leave_request(
        db_session, pending_leave_request.id
    )

    assert request.id == pending_leave_request.id
    assert request.employee_id == test_user.id
    assert request.status == LeaveStatus.PENDING


@pytest.mark.asyncio
async def test_process_leave_request_approval(
    db_session, test_admin, pending_leave_request
):
    """Test approving a leave request"""
    result = await LeaveRequestService.process_leave_request(
        db_session,
        pending_leave_request.id,
        test_admin.id,
        LeaveStatus.APPROVED,
        "Approved by admin",
    )

    assert result["status"] == LeaveStatus.APPROVED.value
    assert result["admin_response"]["admin_id"] == test_admin.id
    assert result["admin_response"]["comment"] == "Approved by admin"


@pytest.mark.asyncio
async def test_cancel_leave_request(db_session, test_user, pending_leave_request):
    """Test canceling a leave request"""
    result = await LeaveRequestService.cancel_leave_request(
        db_session, pending_leave_request.id, test_user.id
    )

    assert result["message"] == "Leave request cancelled successfully"

    # Verify the request is actually cancelled
    cancelled_request = LeaveRequestService.get_leave_request(
        db_session, pending_leave_request.id
    )
    assert cancelled_request.status == LeaveStatus.CANCELLED


@pytest.mark.asyncio
async def test_cannot_cancel_approved_request(
    db_session, test_user, approved_leave_request
):
    """Test that an approved request cannot be cancelled"""
    with pytest.raises(HTTPException) as exc_info:
        await LeaveRequestService.cancel_leave_request(
            db_session, approved_leave_request.id, test_user.id
        )

    assert exc_info.value.status_code == 400
    assert "Can only cancel pending requests" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_validate_leave_dates(db_session, test_user):
    """Test validation of leave request dates"""
    invalid_dates_data = {
        "leave_type": LeaveType.VACATION,
        "start_date": datetime.now() - timedelta(days=1),  # Past date
        "end_date": datetime.now() + timedelta(days=1),
        "reason": "Invalid dates",
    }

    with pytest.raises(HTTPException) as exc_info:
        await LeaveRequestService.create_leave_request(
            db_session, invalid_dates_data, test_user.id
        )

    assert exc_info.value.status_code == 400
    assert "Start date cannot be in the past" in str(exc_info.value.detail)
