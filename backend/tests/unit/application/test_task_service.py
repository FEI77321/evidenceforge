from uuid import uuid4

import pytest

from evidenceforge.application.task_service import TaskService
from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.testing import FakeTaskQueue, FakeTaskRepository


@pytest.mark.anyio
async def test_create_task_persists_and_enqueues_the_task() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )

    task = await service.create_task(question="调研 FastAPI 何时应该使用独立任务队列")

    stored_task = await repository.get(task.id)

    assert task.status is TaskStatus.QUEUED
    assert stored_task == task
    assert queue.enqueued_task_ids == [task.id]


@pytest.mark.anyio
async def test_create_task_rejects_a_blank_question_before_enqueueing() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )

    with pytest.raises(ValueError, match="question must not be blank"):
        await service.create_task(question="   ")

    assert queue.enqueued_task_ids == []


@pytest.mark.anyio
async def test_get_task_returns_an_existing_task() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )
    task = ResearchTask.create(question="调研 Celery 的任务重试机制")
    await repository.add(task)

    found_task = await service.get_task(task.id)

    assert found_task == task


@pytest.mark.anyio
async def test_get_task_returns_none_for_unknown_id() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )

    found_task = await service.get_task(uuid4())

    assert found_task is None


@pytest.mark.anyio
async def test_cancel_task_requests_cancellation_and_persists_it() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )
    task = ResearchTask.create(question="调研 Celery 的任务取消机制")
    await repository.add(task)

    task_after_cancel_request = await service.cancel_task(task.id)
    stored_task = await repository.get(task.id)

    assert task_after_cancel_request == task
    assert task_after_cancel_request is not None
    assert task_after_cancel_request.status is TaskStatus.CANCEL_REQUESTED
    assert stored_task == task_after_cancel_request
    assert queue.enqueued_task_ids == []


@pytest.mark.anyio
async def test_cancel_task_returns_none_for_unknown_id() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        queue=queue,
    )

    task_after_cancel_request = await service.cancel_task(uuid4())

    assert task_after_cancel_request is None
    assert queue.enqueued_task_ids == []
