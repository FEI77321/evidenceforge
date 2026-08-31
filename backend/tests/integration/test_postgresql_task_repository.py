import pytest

from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.infrastructure.database import async_session_factory
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)


@pytest.mark.anyio
async def test_add_then_get_returns_the_persisted_task() -> None:
    repository = PostgreSQLTaskRepository(async_session_factory)
    task = ResearchTask.create(question="调研 PostgreSQL 如何保存任务状态")

    await repository.add(task)

    found_task = await repository.get(task.id)

    assert found_task == task


@pytest.mark.anyio
async def test_update_persists_a_task_status_change() -> None:
    repository = PostgreSQLTaskRepository(async_session_factory)
    task = ResearchTask.create(question="调研任务状态更新的持久化方式")
    await repository.add(task)

    task.transition_to(TaskStatus.RUNNING)
    await repository.update(task)

    found_task = await repository.get(task.id)

    assert found_task is not None
    assert found_task.status is TaskStatus.RUNNING
