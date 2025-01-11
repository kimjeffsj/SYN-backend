from datetime import datetime, timedelta

import pytest
from app.features.schedule.bulk_service import BulkScheduleService
from app.models.schedule import Schedule
from app.models.schedule_enums import RepeatFrequency, ScheduleStatus, ShiftType
from fastapi import HTTPException


@pytest.fixture
def basic_schedule_data(test_user):
    """Basic schedule data fixture"""
    start_time = datetime.now().replace(hour=9, minute=0) + timedelta(days=1)
    return {
        "user_id": test_user.id,
        "start_time": start_time,
        "end_time": start_time + timedelta(hours=8),
        "shift_type": ShiftType.MORNING,
        "description": "Test schedule",
    }


@pytest.fixture
def bulk_schedule_data(basic_schedule_data):
    """Bulk schedule creation data"""
    schedules = []
    start_time = basic_schedule_data["start_time"]

    for i in range(3):  # Create 3 schedules
        schedule_data = basic_schedule_data.copy()
        schedule_data["start_time"] = start_time + timedelta(days=i)
        schedule_data["end_time"] = schedule_data["start_time"] + timedelta(hours=8)
        schedules.append(schedule_data)

    return schedules


@pytest.fixture
def repeating_pattern_data(basic_schedule_data):
    """Repeating pattern data"""
    return {
        "type": RepeatFrequency.WEEKLY,
        "interval": 1,
        "days": ["1", "3", "5"],  # Monday, Wednesday, Friday
        "end_date": basic_schedule_data["start_time"] + timedelta(weeks=2),
    }


@pytest.mark.asyncio
async def test_create_bulk_schedules(db_session, test_admin, bulk_schedule_data):
    """Test creating multiple schedules at once"""
    created_schedules = await BulkScheduleService.create_bulk_schedules(
        db_session, bulk_schedule_data, test_admin.id
    )

    assert len(created_schedules) == len(bulk_schedule_data)
    for schedule in created_schedules:
        assert schedule["status"] == ScheduleStatus.CONFIRMED.value
        assert schedule["created_by"] == test_admin.id


@pytest.mark.asyncio
async def test_create_bulk_schedules_with_conflict(
    db_session, test_admin, bulk_schedule_data
):
    """Test bulk creation with conflicting schedules"""
    # Create first set of schedules
    await BulkScheduleService.create_bulk_schedules(
        db_session, bulk_schedule_data, test_admin.id
    )

    # Try to create overlapping schedules
    with pytest.raises(HTTPException) as exc_info:
        await BulkScheduleService.create_bulk_schedules(
            db_session, bulk_schedule_data, test_admin.id
        )

    assert exc_info.value.status_code == 400
    assert "conflict" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_repeating_schedules(
    db_session, test_admin, basic_schedule_data, repeating_pattern_data
):
    """Test creating repeating schedules"""
    created_schedules = await BulkScheduleService.create_repeating_schedules(
        db_session, basic_schedule_data, repeating_pattern_data, test_admin.id
    )

    # Calculate expected number of schedules
    # For 2 weeks, 3 days per week = 6 schedules
    assert len(created_schedules) == 6

    # Verify schedules are created on correct days
    for schedule in created_schedules:
        schedule_date = datetime.fromisoformat(schedule["start_time"])
        assert str(schedule_date.weekday()) in repeating_pattern_data["days"]


@pytest.mark.asyncio
async def test_validate_schedules(db_session, bulk_schedule_data, test_user):
    """Test schedule validation"""
    # Valid case
    is_valid = await BulkScheduleService.validate_schedules(
        db_session, bulk_schedule_data
    )
    assert is_valid is True

    # Invalid case - non-existent user
    invalid_data = bulk_schedule_data.copy()
    invalid_data[0]["user_id"] = 99999

    with pytest.raises(HTTPException) as exc_info:
        await BulkScheduleService.validate_schedules(db_session, invalid_data)

    assert exc_info.value.status_code == 400
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_check_schedule_conflict(db_session, test_user, basic_schedule_data):
    """Test schedule conflict checking"""
    # Create initial schedule
    schedule = Schedule(**basic_schedule_data, created_by=test_user.id)
    db_session.add(schedule)
    db_session.commit()

    # Check for conflict - same time
    has_conflict = await BulkScheduleService._check_schedule_conflict(
        db_session,
        test_user.id,
        basic_schedule_data["start_time"],
        basic_schedule_data["end_time"],
    )
    assert has_conflict is True

    # Check for no conflict - different time
    no_conflict_start = basic_schedule_data["start_time"] + timedelta(days=1)
    no_conflict_end = no_conflict_start + timedelta(hours=8)

    has_conflict = await BulkScheduleService._check_schedule_conflict(
        db_session, test_user.id, no_conflict_start, no_conflict_end
    )
    assert has_conflict is False
