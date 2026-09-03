from uuid import UUID

from evidenceforge.infrastructure.celery_app import celery_app


class CeleryTaskQueue:
    """通过 Celery 将调研任务投递到 Redis。"""

    async def enqueue(self, task_id: UUID) -> None:
        """把指定任务的 ID 发送给后台 Worker。"""

        celery_app.send_task(
            "evidenceforge.run_research_task",
            args=[str(task_id)],
            queue="research",
        )