from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """Base class for all models"""

    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True, default=None
    )
