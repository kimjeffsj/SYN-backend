from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class BaseEventType(str, Enum):
    pass


@dataclass
class Event:
    type: BaseEventType
    data: dict
    timestamp: datetime = datetime.now(timezone.utc)
