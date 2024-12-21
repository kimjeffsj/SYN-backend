from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine
from app.core.events import event_bus
from app.features.admin_dashboard import router as admin_dashboard_router
from app.features.announcements import router as announcement_router
from app.features.auth import router as auth_router
from app.features.employee_dashboard import router as employee_dashboard_router
from app.features.employee_management import department_router as department_router
from app.features.employee_management import position_router as position_router
from app.features.employee_management import router as employee_router
from app.features.notifications import router as notification_router
from app.features.notifications import ws_router
from app.features.notifications.events import register_notification_handlers
from app.features.notifications.ws_manager import notification_manager
from app.features.schedule import admin_router as schedule_admin_router
from app.features.schedule import router as schedule_router
from app.features.shift_trade import router as shift_trade_router
from app.models import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)


#
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute the code start up
    register_notification_handlers(event_bus)

    await notification_manager.start()
    yield
    # Execute the code shutdown
    await notification_manager.stop()


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Auth", "description": "Authentication and authorization operations"},
        {
            "name": "Admin",
            "description": "Administrative operations for managing schedules and users",
        },
        {
            "name": "Employee",
            "description": "Employee operations for viewing schedules and managing profile",
        },
        {
            "name": "Dashboard",
            "description": "Dashboard views and operations for both admin and employees",
        },
        {
            "name": "Employee Management",
            "description": "Manage employees, departments, and positions",
        },
        {
            "name": "Announcements",
            "description": "System announcements and notifications",
        },
        {"name": "Notifications", "description": "Real-time notifications and alerts"},
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# Schedule routers
app.include_router(schedule_router, prefix="/schedules", tags=["Employee"])

app.include_router(schedule_admin_router, prefix="/admin/schedules", tags=["Admin"])


# Dashboard routers
app.include_router(
    employee_dashboard_router,
    prefix="/dashboard",
    tags=["Dashboard", "Employee"],
)

app.include_router(
    admin_dashboard_router, prefix="/admin/dashboard", tags=["Dashboard", "Admin"]
)

# Employee management routers
app.include_router(
    employee_router, prefix="/admin/employees", tags=["Employee Management"]
)

app.include_router(
    department_router,
    prefix="/admin/departments",
    tags=["Employee Management"],
)
app.include_router(
    position_router, prefix="/admin/positions", tags=["Employee Management"]
)


app.include_router(shift_trade_router, prefix="/trades", tags=["Shift Trade"])

app.include_router(announcement_router, prefix="/announcements", tags=["Announcements"])

app.include_router(notification_router, prefix="/notifications", tags=["Notifications"])

app.mount("/ws", ws_router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
