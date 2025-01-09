from datetime import datetime, timedelta

import pytest
from app.features.schedule.service import ScheduleService
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus, ShiftType
from fastapi import HTTPException


@pytest.fixture
def basic_schedule_data(test_user):
    """Create basic schedule data"""
    start_time = datetime.now().replace(hour=9, minute=0) + timedelta(days=1)
    return {
        "user_id": test_user.id,
        "start_time": start_time,
        "end_time": start_time + timedelta(hours=8),
        "shift_type": ShiftType.MORNING,
        "description": "Test schedule",
    }


@pytest.mark.asyncio
async def test_create_schedule(db_session, test_admin, basic_schedule_data):
    """Test schedule creation"""
    schedule = await ScheduleService.create_schedule(
        db_session, basic_schedule_data, test_admin.id
    )

    assert schedule is not None
    assert schedule["user_id"] == basic_schedule_data["user_id"]
    assert schedule["shift_type"] == basic_schedule_data["shift_type"].value
    assert schedule["status"] == ScheduleStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_create_schedule_with_conflict(
    db_session, test_admin, basic_schedule_data
):
    """Test schedule creation with time conflict"""
    # Create first schedule
    await ScheduleService.create_schedule(
        db_session, basic_schedule_data, test_admin.id
    )

    # Try to create overlapping schedule
    conflicting_data = basic_schedule_data.copy()
    conflicting_data["start_time"] = basic_schedule_data["start_time"] + timedelta(
        hours=2
    )

    with pytest.raises(HTTPException) as exc_info:
        await ScheduleService.create_schedule(
            db_session, conflicting_data, test_admin.id
        )

    assert exc_info.value.status_code == 400
    assert "conflict" in str(exc_info.value.detail).lower()


def test_get_schedule(db_session, test_admin, basic_schedule_data):
    """Test retrieving a specific schedule"""
    # Create schedule first
    schedule = Schedule(**basic_schedule_data, created_by=test_admin.id)
    db_session.add(schedule)
    db_session.commit()

    # Retrieve schedule
    retrieved = ScheduleService.get_schedule(db_session, schedule.id)
    assert retrieved is not None
    assert retrieved.user_id == basic_schedule_data["user_id"]
    assert retrieved.shift_type == basic_schedule_data["shift_type"]


def test_get_nonexistent_schedule(db_session):
    """Test retrieving a nonexistent schedule"""
    with pytest.raises(HTTPException) as exc_info:
        ScheduleService.get_schedule(db_session, 999999)

    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_schedule_status(db_session, test_admin, basic_schedule_data):
    """Test updating schedule status"""
    # Create schedule first
    schedule = Schedule(**basic_schedule_data, created_by=test_admin.id)
    db_session.add(schedule)
    db_session.commit()

    # Update status
    updated = await ScheduleService.update_schedule_status(
        db_session, schedule.id, ScheduleStatus.COMPLETED.value
    )

    assert updated.status == ScheduleStatus.COMPLETED
