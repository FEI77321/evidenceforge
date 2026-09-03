from celery import Celery

from evidenceforge.infrastructure.config import Settings

settings = Settings()

celery_app = Celery(
    "evidenceforge",
    broker=settings.redis_broker_url,
    backend=settings.redis_result_backend_url,
)

celery_app.conf.update(
    task_default_queue="research",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    timezone="Asia/Shanghai",
    enable_utc=True,
)