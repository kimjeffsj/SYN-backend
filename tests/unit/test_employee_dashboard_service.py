from datetime import datetime, timedelta, timezone

import pytest
from app.features.employee_dashboard.service import EmployeeDashboardService
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus, ShiftType
from app.models.user import User
from fastapi import HTTPException


@pytest.fixture
def employee_data():
    """Basic employee data"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "dummy_hash",
        "role": "employee",
        "department": "IT",
        "position": "Developer",
        "leave_balance": 10,
        "is_active": True,
        "is_on_leave": False,
    }


@pytest.fixture
def setup_employee(db_session, employee_data):
    """Create test employee"""
    user = User(**employee_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def setup_schedules(db_session, setup_employee):
    """Create test schedules with various states"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    schedules = []

    # Today's schedule
    schedule = Schedule(
        user_id=setup_employee.id,
        start_time=today_start.replace(hour=9),
        end_time=today_start.replace(hour=17),
        shift_type=ShiftType.MORNING,
        status=ScheduleStatus.CONFIRMED,
        created_by=setup_employee.id,
    )
    schedules.append(schedule)

    # Past schedules
    for i in range(1, 4):  # 3 completed schedules
        schedule = Schedule(
            user_id=setup_employee.id,
            start_time=(today_start - timedelta(days=i)).replace(hour=9),
            end_time=(today_start - timedelta(days=i)).replace(hour=17),
            shift_type=ShiftType.MORNING,
            status=ScheduleStatus.COMPLETED,
            created_by=setup_employee.id,
        )
        schedules.append(schedule)

    # Future schedules
    for i in range(1, 4):  # 3 upcoming schedules
        schedule = Schedule(
            user_id=setup_employee.id,
            start_time=(today_start + timedelta(days=i)).replace(hour=9),
            end_time=(today_start + timedelta(days=i)).replace(hour=17),
            shift_type=ShiftType.MORNING,
            status=ScheduleStatus.CONFIRMED,
            created_by=setup_employee.id,
        )
        schedules.append(schedule)

    for schedule in schedules:
        db_session.add(schedule)
    db_session.commit()

    return schedules


@pytest.mark.asyncio
async def test_get_dashboard_data_success(db_session, setup_employee, setup_schedules):
    """Test dashboard data retrieval"""
    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )

    # Validate employee information
    assert dashboard_data["employee"]["id"] == setup_employee.id
    assert dashboard_data["employee"]["name"] == setup_employee.full_name
    assert dashboard_data["employee"]["department"] == "IT"
    assert dashboard_data["employee"]["position"] == "Developer"

    # Validate statistics
    assert dashboard_data["stats"]["leaveBalance"] == 10
    assert dashboard_data["stats"]["completedShifts"] == 3  # 3 completed schedules
    assert dashboard_data["stats"]["upcomingShifts"] == 3  # 3 upcoming schedules
    assert dashboard_data["stats"]["totalHours"] == 24.0  # 3 completed 8-hour schedules

    # Validate schedule information
    assert dashboard_data["todaySchedule"] is not None
    assert len(dashboard_data["weeklySchedule"]) > 0


@pytest.mark.asyncio
async def test_get_dashboard_data_no_schedules(db_session, setup_employee):
    """Test dashboard data retrieval with no schedules"""
    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )

    assert dashboard_data["stats"]["completedShifts"] == 0
    assert dashboard_data["stats"]["upcomingShifts"] == 0
    assert dashboard_data["stats"]["totalHours"] == 0
    assert dashboard_data["todaySchedule"] is None
    assert len(dashboard_data["weeklySchedule"]) == 0


@pytest.mark.asyncio
async def test_get_dashboard_data_user_not_found(db_session):
    """Test dashboard data retrieval for non-existent employee"""
    with pytest.raises(HTTPException) as exc_info:
        await EmployeeDashboardService.get_dashboard_data(db_session, 999)

    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_dashboard_data_inactive_user(db_session, setup_employee):
    """Test dashboard data retrieval for inactive employee"""
    # Deactivate employee
    setup_employee.is_active = False
    db_session.commit()

    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )

    assert not dashboard_data["employee"]["is_active"]


@pytest.mark.asyncio
async def test_get_dashboard_data_on_leave(db_session, setup_employee, setup_schedules):
    """Test dashboard data retrieval for employee on leave"""
    # Change employee status to on leave
    setup_employee.is_on_leave = True
    db_session.commit()

    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )

    assert dashboard_data["employee"]["is_on_leave"]
    # Existing schedule data should be retained even when on leave
    assert len(dashboard_data["weeklySchedule"]) > 0


@pytest.mark.asyncio
async def test_weekly_schedule_calculation(db_session, setup_employee, setup_schedules):
    """Test weekly schedule calculation"""
    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )
    weekly_schedule = dashboard_data["weeklySchedule"]

    now = datetime.now(timezone.utc)
    week_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=now.weekday()
    )
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    for schedule in weekly_schedule:
        # Convert ISO format string to timezone-aware datetime
        schedule_date = datetime.fromisoformat(schedule["start_time"])
        # Add UTC timezone if not present
        if schedule_date.tzinfo is None:
            schedule_date = schedule_date.replace(tzinfo=timezone.utc)

        assert week_start <= schedule_date <= week_end


@pytest.mark.asyncio
async def test_total_hours_calculation(db_session, setup_employee, setup_schedules):
    """Test total working hours calculation"""
    dashboard_data = await EmployeeDashboardService.get_dashboard_data(
        db_session, setup_employee.id
    )

    expected_hours = 3 * 8.0
    assert dashboard_data["stats"]["totalHours"] == expected_hours
