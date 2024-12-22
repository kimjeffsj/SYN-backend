"""add demo data

Revision ID: 9416a4134a0c
Revises: bac2490fb76a
Create Date: 2024-12-22 12:44:15.674718

"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op
from app.models.schedule_enums import ScheduleStatus, ShiftType

# revision identifiers, used by Alembic.
revision: str = "9416a4134a0c"
down_revision: Union[str, None] = "bac2490fb76a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# Create timestamp helpers
now = datetime.now(timezone.utc)
past_date = now - timedelta(days=15)  # Start from 15 days ago
future_date = now + timedelta(days=45)  # Until 45 days in future


def generate_schedule_data(
    user_ids: List[int], admin_id: int, start_date: datetime, end_date: datetime
) -> List[dict]:
    schedules = []
    shift_types = ["MORNING", "AFTERNOON", "EVENING"]
    current_date = start_date

    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            for user_id in user_ids:
                shift_type = random.choice(shift_types)
                if shift_type == ShiftType.MORNING.value:
                    start_time = current_date.replace(hour=7)
                    end_time = current_date.replace(hour=15)
                elif shift_type == ShiftType.AFTERNOON.value:
                    start_time = current_date.replace(hour=11)
                    end_time = current_date.replace(hour=19)
                else:
                    start_time = current_date.replace(hour=17)
                    end_time = current_date.replace(hour=23)

                schedules.append(
                    {
                        "user_id": user_id,
                        "created_by": admin_id,
                        "start_time": start_time,
                        "end_time": end_time,
                        "shift_type": shift_type,  # 대문자 값 사용
                        "status": "CONFIRMED",  # 대문자 값 사용
                        "created_at": past_date,
                        "updated_at": past_date,
                    }
                )
        current_date += timedelta(days=1)

    return schedules


def upgrade():
    # Create demo users (15 employees + 1 admin)
    departments = ["Development", "Product", "Design", "QA"]
    positions = {
        "Development": ["Senior Developer", "Junior Developer"],
        "Product": ["Product Manager"],
        "Design": ["UI/UX Designer"],
        "QA": ["QA Engineer"],
    }

    users = [
        {
            "id": 1,
            "email": "admin@demo.com",
            "hashed_password": hash_password("demo1234"),
            "full_name": "Demo Admin",
            "department": "Development",
            "position": "CTO",
            "role": "admin",
            "is_active": True,
            "is_demo": True,
            "leave_balance": 15,
        }
    ]

    # Generate employee data
    employee_data = [
        ("john.doe@demo.com", "John Doe", "Development", "Senior Developer"),
        ("jane.smith@demo.com", "Jane Smith", "Development", "Senior Developer"),
        ("alex.kim@demo.com", "Alex Kim", "Development", "Junior Developer"),
        ("sarah.lee@demo.com", "Sarah Lee", "Development", "Junior Developer"),
        ("mike.product@demo.com", "Mike Johnson", "Product", "Product Manager"),
        ("emma.product@demo.com", "Emma Wilson", "Product", "Product Manager"),
        ("david.design@demo.com", "David Chen", "Design", "UI/UX Designer"),
        ("sophia.design@demo.com", "Sophia Park", "Design", "UI/UX Designer"),
        ("lily.design@demo.com", "Lily Zhang", "Design", "UI/UX Designer"),
        ("tom.qa@demo.com", "Tom Brown", "QA", "QA Engineer"),
        ("grace.qa@demo.com", "Grace Liu", "QA", "QA Engineer"),
        ("james.qa@demo.com", "James Wilson", "QA", "QA Engineer"),
        ("olivia.qa@demo.com", "Olivia Davis", "QA", "QA Engineer"),
        ("ryan.qa@demo.com", "Ryan Taylor", "QA", "QA Engineer"),
    ]

    for i, (email, name, dept, pos) in enumerate(employee_data, start=2):
        users.append(
            {
                "id": i,
                "email": email,
                "hashed_password": hash_password("demo1234"),
                "full_name": name,
                "department": dept,
                "position": pos,
                "role": "employee",
                "is_active": True,
                "is_demo": True,
                "leave_balance": 15,
            }
        )

    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", sa.Integer),
            sa.column("email", sa.String),
            sa.column("hashed_password", sa.String),
            sa.column("full_name", sa.String),
            sa.column("department", sa.String),
            sa.column("position", sa.String),
            sa.column("role", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("is_demo", sa.Boolean),
            sa.column("leave_balance", sa.Integer),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        [{**user, "created_at": past_date, "updated_at": past_date} for user in users],
    )

    # Create schedules
    user_ids = [user["id"] for user in users if user["role"] == "employee"]
    admin_id = users[0]["id"]  # First user is admin
    schedules = generate_schedule_data(user_ids, admin_id, past_date, future_date)

    op.bulk_insert(
        sa.table(
            "schedules",
            sa.column("user_id", sa.Integer),
            sa.column("created_by", sa.Integer),
            sa.column("start_time", sa.DateTime),
            sa.column("end_time", sa.DateTime),
            sa.column("shift_type", sa.String),
            sa.column("status", sa.String),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        schedules,
    )

    # Create sample announcements
    announcements = [
        {
            "id": 1,
            "title": "Welcome to SYN Demo",
            "content": "Welcome to our scheduling system demo! Feel free to explore all features and functionalities.",
            "created_by": admin_id,
            "priority": "normal",
        },
        {
            "id": 2,
            "title": "New Project Kickoff",
            "content": "We're starting a new project next week. Team leads will schedule briefing meetings soon.",
            "created_by": admin_id,
            "priority": "high",
        },
        {
            "id": 3,
            "title": "Office Updates",
            "content": "We've updated our meeting room booking system. Please check the new guidelines.",
            "created_by": admin_id,
            "priority": "normal",
        },
    ]

    op.bulk_insert(
        sa.table(
            "announcements",
            sa.column("id", sa.Integer),
            sa.column("title", sa.String),
            sa.column("content", sa.String),
            sa.column("created_by", sa.Integer),
            sa.column("priority", sa.String),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        [
            {**announcement, "created_at": past_date, "updated_at": past_date}
            for announcement in announcements
        ],
    )

    # Create sample leave requests
    leave_requests = [
        {
            "id": 1,
            "employee_id": 2,  # John Doe
            "start_date": (now + timedelta(days=10)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            "end_date": (now + timedelta(days=12)).replace(
                hour=23, minute=59, second=59
            ),
            "status": "APPROVED",
            "reason": "Annual leave",
            "leave_type": "VACATION",
            "admin_id": admin_id,
            "admin_comment": "Approved for annual leave",
            "processed_at": now,
        },
        {
            "id": 2,
            "employee_id": 3,  # Jane Smith
            "start_date": (now + timedelta(days=15)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            "end_date": (now + timedelta(days=15)).replace(
                hour=23, minute=59, second=59
            ),
            "status": "PENDING",
            "reason": "Personal appointment",
            "leave_type": "ON_LEAVE",
            "admin_id": None,  # PENDING 상태이므로 None으로 설정
            "admin_comment": None,  # PENDING 상태이므로 None으로 설정
            "processed_at": None,
        },
    ]

    op.bulk_insert(
        sa.table(
            "leave_requests",
            sa.column("id", sa.Integer),
            sa.column("employee_id", sa.Integer),
            sa.column("start_date", sa.DateTime),
            sa.column("end_date", sa.DateTime),
            sa.column("status", sa.String),
            sa.column("reason", sa.String),
            sa.column("leave_type", sa.String),
            sa.column("admin_id", sa.Integer),
            sa.column("admin_comment", sa.String),
            sa.column("processed_at", sa.DateTime),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        [
            {**request, "created_at": past_date, "updated_at": past_date}
            for request in leave_requests
        ],
    )


def downgrade():
    # Remove all seed data in reverse order
    op.execute("DELETE FROM leave_requests WHERE id IN (1, 2)")
    op.execute(
        "DELETE FROM schedules WHERE created_by IN (SELECT id FROM users WHERE is_demo = true)"
    )
    op.execute("DELETE FROM announcements WHERE id IN (1, 2, 3)")
    op.execute("DELETE FROM users WHERE is_demo = true")
