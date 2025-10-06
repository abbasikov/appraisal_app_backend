from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "appraisal_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.photo_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    result_expires=3600,  # 1 hour
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure periodic tasks if needed
celery_app.conf.beat_schedule = {
    # Add any periodic tasks here if needed
}

celery_app.conf.timezone = 'UTC'
