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
    "cleanup-old-notifications": {
        "task": "app.features.notifications.tasks.cleanup_old_notifications",
        "schedule": 86400.0,
    },
}
