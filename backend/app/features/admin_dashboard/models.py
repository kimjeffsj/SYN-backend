from app.core.database import Base
from sqlalchemy import Column, DateTime, Integer, func


class AdminDashboardStats(Base):
    __tablename__ = "admin_dashboard_stats"

    id = Column(Integer, primary_key=True, index=True)
    employee_count = Column(Integer, default=0)
    active_count = Column(Integer, default=0)
    on_leave_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
