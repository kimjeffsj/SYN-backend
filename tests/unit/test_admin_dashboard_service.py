from datetime import datetime, timedelta

import pytest
from app.features.admin_dashboard.service import AdminDashboardService
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus, ShiftType
from app.models.user import User


@pytest.fixture
def setup_employees(db_session):
    """Create test employees with various states"""
    employees = []
    departments = ["IT", "HR", "Sales"]
    positions = ["Engineer", "Manager", "Associate"]

    for i in range(5):
        employee = User(
            email=f"employee{i}@test.com",
            full_name=f"Test Employee {i}",
            role="employee",
            hashed_password="dummy_hash",
            department=departments[i % len(departments)],
            position=positions[i % len(positions)],
            is_active=True,
            is_on_leave=(i == 1),  # One employee on leave
            leave_balance=10,
        )
        employees.append(employee)
        db_session.add(employee)

    db_session.commit()
    return employees


@pytest.fixture
def setup_schedules(db_session, setup_employees, test_admin):
    """Create test schedules with various states"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    schedules = []

    # Today's schedules
    for i, employee in enumerate(setup_employees):
        # Morning shift
        if i % 3 == 0:
            schedule = Schedule(
                user_id=employee.id,
                start_time=today_start.replace(hour=9),
                end_time=today_start.replace(hour=17),
                shift_type=ShiftType.MORNING,
                status=ScheduleStatus.CONFIRMED,
                created_by=test_admin.id,
            )
            schedules.append(schedule)

        # Afternoon shift with conflict
        elif i % 3 == 1:
            schedule1 = Schedule(
                user_id=employee.id,
                start_time=today_start.replace(hour=13),
                end_time=today_start.replace(hour=21),
                shift_type=ShiftType.AFTERNOON,
                status=ScheduleStatus.CONFIRMED,
                created_by=test_admin.id,
            )
            # Conflicting schedule
            schedule2 = Schedule(
                user_id=employee.id,
                start_time=today_start.replace(hour=20),
                end_time=today_start.replace(hour=23),
                shift_type=ShiftType.EVENING,
                status=ScheduleStatus.PENDING,
                created_by=test_admin.id,
            )
            schedules.extend([schedule1, schedule2])

        # Future schedule
        else:
            schedule = Schedule(
                user_id=employee.id,
                start_time=(today_start + timedelta(days=1)).replace(hour=9),
                end_time=(today_start + timedelta(days=1)).replace(hour=17),
                shift_type=ShiftType.MORNING,
                status=ScheduleStatus.PENDING,
                created_by=test_admin.id,
            )
            schedules.append(schedule)

    for schedule in schedules:
        db_session.add(schedule)
    db_session.commit()
    return schedules


@pytest.fixture
def setup_notifications(db_session, setup_employees):
    """Create test notifications with various states"""
    notifications = []
    for employee in setup_employees:
        notifications.extend(
            [
                Notification(
                    user_id=employee.id,
                    type=NotificationType.SCHEDULE_CHANGE,
                    title="Schedule Update",
                    message=f"Schedule updated for {employee.full_name}",
                    status=NotificationStatus.SENT,
                    created_at=datetime.now(),
                    is_read=False,
                ),
                Notification(
                    user_id=employee.id,
                    type=NotificationType.SYSTEM,
                    title="System Notice",
                    message="System maintenance scheduled",
                    status=NotificationStatus.SENT,
                    created_at=datetime.now() - timedelta(days=1),
                    is_read=True,
                ),
            ]
        )

    for notification in notifications:
        db_session.add(notification)
    db_session.commit()
    return notifications


@pytest.mark.asyncio
async def test_get_dashboard_stats(db_session, setup_employees, setup_schedules):
    """Test comprehensive dashboard statistics"""
    stats = await AdminDashboardService.get_dashboard_stats(db_session)

    # Employee stats verification
    assert stats["employees"]["total"] == len(setup_employees)
    assert stats["employees"]["onLeave"] == 1  # One employee set on leave
    assert stats["employees"]["active"] == len(setup_employees) - 1

    # Schedule stats verification
    today_schedules = [
        s for s in setup_schedules if s.start_time.date() == datetime.now().date()
    ]
    pending_schedules = [
        s for s in setup_schedules if s.status == ScheduleStatus.PENDING
    ]

    assert stats["schedules"]["today"] == len(today_schedules)
    assert stats["schedules"]["pending"] == len(pending_schedules)
    assert stats["schedules"]["conflicts"] > 0  # We created conflicting schedules


@pytest.mark.asyncio
async def test_get_recent_updates(db_session, setup_notifications, setup_schedules):
    """Test recent updates with various types of activities"""
    updates = await AdminDashboardService.get_recent_updates(db_session, limit=5)

    assert len(updates) > 0
    for update in updates:
        assert all(
            key in update
            for key in ["id", "type", "title", "description", "timestamp", "status"]
        )

        if update["type"] == "SCHEDULE_CHANGE":
            assert "Schedule" in update["description"]
        elif update["type"] == "NOTIFICATION":
            assert update["title"] == "New Notification"


@pytest.mark.asyncio
async def test_get_employee_overview_detailed(
    db_session, setup_employees, setup_schedules
):
    """Test detailed employee overview with various states"""
    overview = await AdminDashboardService.get_employee_overview(db_session)

    assert len(overview) == len(setup_employees)

    for emp in overview:
        assert all(
            key in emp
            for key in [
                "id",
                "name",
                "position",
                "department",
                "status",
                "currentShift",
            ]
        )

        # Verify status logic
        original_emp = next(e for e in setup_employees if e.id == emp["id"])
        expected_status = "onLeave" if original_emp.is_on_leave else "active"
        assert emp["status"] == expected_status

        # Verify current shift info
        if emp["currentShift"]:
            assert ":" in emp["currentShift"]  # Time format verification


@pytest.mark.asyncio
async def test_get_current_shift_scenarios(
    db_session, setup_employees, setup_schedules
):
    """Test current shift detection for various scenarios"""
    emp_id = setup_employees[0].id

    # Test current shift during work hours
    current_shift = await AdminDashboardService._get_current_shift(db_session, emp_id)

    if current_shift:
        assert "-" in current_shift
        assert len(current_shift.split("-")) == 2
        start, end = current_shift.split("-")
        assert ":" in start and ":" in end

    # Test with no current shift
    future_shift_emp = next(
        emp
        for emp in setup_employees
        if not any(
            s.start_time.date() == datetime.now().date()
            for s in setup_schedules
            if s.user_id == emp.id
        )
    )
    no_current = await AdminDashboardService._get_current_shift(
        db_session, future_shift_emp.id
    )
    assert no_current is None
