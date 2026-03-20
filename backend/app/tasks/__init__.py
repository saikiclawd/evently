"""
Evently — Celery Task Configuration
"""
import os
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "evently",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# ── Periodic Tasks (Celery Beat) ──
celery_app.conf.beat_schedule = {
    "send-payment-reminders": {
        "task": "app.tasks.payment_reminders.send_due_reminders",
        "schedule": crontab(minute=0, hour="*/1"),  # Every hour
    },
    "sync-website-inventory": {
        "task": "app.tasks.inventory_sync.sync_availability",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "monthly-business-insights": {
        "task": "app.tasks.monthly_insights.generate_report",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),  # 1st of month, 8 AM
    },
    "quickbooks-batch-sync": {
        "task": "app.tasks.quickbooks_sync.batch_sync",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
