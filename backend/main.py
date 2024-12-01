from app.core.config import settings
from app.core.database import engine
from app.features.admin_dashboard import router as admin_dashboard_router
from app.features.auth import router as auth_router
from app.features.employee_dashboard import router as employee_dashboard_router
from app.features.schedule import admin_router as schedule_admin_router
from app.features.schedule import router as schedule_router
from app.models import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(schedule_router, prefix="/schedules", tags=["schedules"])
app.include_router(
    schedule_admin_router, prefix="/admin/schedules", tags=["admin", "schedules"]
)
app.include_router(
    employee_dashboard_router,
    prefix="/employee/dashboard",
    tags=["dashboard"],
)
app.include_router(
    admin_dashboard_router, prefix="/admin/dashboard", tags=["admin", "dashboard"]
)


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
