import asyncio
from uuid import UUID

from celery.utils.log import get_task_logger

from evidenceforge.domain.tasks import TaskStatus
from evidenceforge.infrastructure.celery_app import celery_app
from evidenceforge.infrastructure.database import (
    async_engine,
    async_session_factory,
)
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)

logger = get_task_logger(__name__)


@celery_app.task(name="evidenceforge.run_research_task")
def run_research_task(task_id: str) -> str:
    """由 Celery Worker 在后台执行一条调研任务。"""

    return asyncio.run(_process_research_task(task_id))


async def _process_research_task(task_id: str) -> str:
    """执行任务状态流转；后续会在这里接入真实调研流程。"""

    repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )

    try:
        task = await repository.get(UUID(task_id))
        if task is None:
            logger.warning("research task %s does not exist", task_id)
            return "missing"

        if task.status is TaskStatus.CANCEL_REQUESTED:
            task.transition_to(TaskStatus.CANCELED)
            await repository.update(task)
            return task.status.value

        if task.status is not TaskStatus.QUEUED:
            logger.info(
                "research task %s is already %s",
                task_id,
                task.status.value,
            )
            return task.status.value

        task.transition_to(TaskStatus.RUNNING)
        await repository.update(task)

        logger.info("research task %s is running", task_id)

        # Day 5 的 Stub：这里以后会替换为真正的调研、检索和证据整理流程。
        await asyncio.sleep(0)

        current_task = await repository.get(task.id)
        if current_task is None:
            return "missing"

        if current_task.status is TaskStatus.CANCEL_REQUESTED:
            current_task.transition_to(TaskStatus.CANCELED)
        elif current_task.status is TaskStatus.RUNNING:
            current_task.transition_to(TaskStatus.COMPLETED)

        await repository.update(current_task)

        logger.info(
            "research task %s finished with status %s",
            task_id,
            current_task.status.value,
        )

        return current_task.status.value
    finally:
        await async_engine.dispose()