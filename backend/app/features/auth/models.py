from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func


class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String)  # "admin" or "employee"
    is_active = Column(Boolean, default=True)
    requires_password_change = Column(Boolean, default=False)
    last_password_change = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.id}: {self.email}>"
