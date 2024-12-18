from enum import Enum


class ShiftType(str, Enum):
    """Types of work shifts"""

    MORNING = "morning"  # 0700-1500
    AFTERNOON = "afternoon"  # 1100-1900
    EVENING = "evening"  # 1700-2300


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
