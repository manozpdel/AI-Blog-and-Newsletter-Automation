from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ai_content_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.content_tasks",
        "app.tasks.scheduled_tasks",  # Added in Task 3
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_extended=True,
    task_track_started=True,
)

# --- Added in Task 3: Celery Beat schedule ---
celery_app.conf.beat_schedule = {
    "daily_content_generation": {
        "task": "content.daily_content_generation",
        "schedule": crontab(hour=6, minute=0),  # every day at 06:00 UTC
    },
}