from enum import Enum


class ShiftType(str, Enum):
    """Types of work shifts"""

    MORNING = "morning"  # 0800-1600
    AFTERNOON = "afternoon"  # 1200-2000
    EVENING = "evening"  # 1700-2200
    FULL_DAY = "full_day"  # 0800-1800


class ScheduleStatus(str, Enum):
    """Status of schedule"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class RepeatFrequency(str, Enum):
    """Frequency of schedule repetition"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
