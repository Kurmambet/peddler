# backend/app/celery_app.py
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "peddler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.message_tasks", "app.tasks.media_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_acks_late=True,  # Подтверждать задачу после выполнения
    task_reject_on_worker_lost=True,
    worker_pool="solo" if settings.DEBUG else "prefork",  # Не использовать prefork на Windows
)

# Автообнаружение задач
celery_app.autodiscover_tasks(["app.tasks"])
