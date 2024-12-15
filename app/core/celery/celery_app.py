from app.core.config import settings
from celery import Celery

celery_app = Celery(
    "syn",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.features.notifications.tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_queues={
        "notifications": {
            "exchange": "notifications",
            "routing_key": "notification.#",
        },
    },
    task_default_queue="notifications",
    task_soft_time_limit=3600,
)


celery_app.conf.beat_schedule = {
    "retry-failed-notifications": {
        "task": "notifications.retry_failed",
        "schedule": 300.0,  # 5 minutes
    },
    "cleanup-old-notifications": {
        "task": "notifications.cleanup_old",
        "schedule": 86400.0,  # 24 hours
    },
}
