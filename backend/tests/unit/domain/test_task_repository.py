import pytest

from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.testing import FakeTaskRepository


@pytest.mark.anyio
async def test_task_repository_returns_an_added_task() -> None:
    repository = FakeTaskRepository()
    task = ResearchTask.create(question="调研 FastAPI 的独立任务队列方案")

    await repository.add(task)

    found_task = await repository.get(task.id)

    assert found_task == task


@pytest.mark.anyio
async def test_task_repository_returns_an_updated_task() -> None:
    repository = FakeTaskRepository()
    task = ResearchTask.create(question="调研 FastAPI 的独立任务队列方案")

    await repository.add(task)

    updated_task = ResearchTask.create(
        question=task.question,
        task_id=task.id,
    )
    updated_task.transition_to(TaskStatus.RUNNING)

    await repository.update(updated_task)

    found_task = await repository.get(task.id)

    assert found_task == updated_task
    assert found_task is not None
    assert found_task.status is TaskStatus.RUNNING
