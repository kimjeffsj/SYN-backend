from app.core.config import settings
from app.core.database import engine
from app.features.admin_dashboard import router as admin_dashboard_router
from app.features.announcements import router as announcement_router
from app.features.auth import router as auth_router
from app.features.employee_dashboard import router as employee_dashboard_router
from app.features.notifications import router as notification_router
from app.features.notifications import ws_router
from app.features.notifications.ws_manager import notification_manager
from app.features.schedule import admin_router as schedule_admin_router
from app.features.schedule import router as schedule_router
from app.features.shift_trade import router as shift_trade_router
from app.models import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
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
            "name": "Announcements",
            "description": "System announcements and notifications",
        },
        {"name": "Notification", "description": "Notifications"},
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

# Routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

app.include_router(schedule_router, prefix="/schedules", tags=["Employee"])

app.include_router(schedule_admin_router, prefix="/admin/schedules", tags=["Admin"])

app.include_router(
    employee_dashboard_router,
    prefix="/dashboard",
    tags=["Dashboard", "Employee"],
)

app.include_router(
    admin_dashboard_router, prefix="/admin/dashboard", tags=["Dashboard", "Admin"]
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


@app.on_event("startup")
async def startup_event():
    await notification_manager.start()


@app.on_event("shutdown")
async def shutdown_event():
    await notification_manager.stop()
