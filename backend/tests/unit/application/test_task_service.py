from uuid import uuid4

import pytest

from evidenceforge.application.task_service import TaskService
from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.testing import (
    FakeTaskEventRepository,
    FakeTaskQueue,
    FakeTaskRepository,
)


@pytest.mark.anyio
async def test_create_task_persists_emits_created_event_and_enqueues_the_task() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=queue,
    )

    task = await service.create_task(
        question="调研 FastAPI 何时应该使用独立任务队列",
    )
    stored_task = await repository.get(task.id)

    assert task.status is TaskStatus.QUEUED
    assert stored_task == task
    assert queue.enqueued_task_ids == [task.id]
    assert len(event_repository.events) == 1

    created_event = event_repository.events[0]

    assert created_event.task_id == task.id
    assert created_event.sequence == 1
    assert created_event.event_type is TaskEventType.CREATED
    assert created_event.stage is None
    assert created_event.payload == {"status": "queued"}



@pytest.mark.anyio
async def test_create_task_rejects_a_blank_question_before_enqueueing() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=queue,
    )

    with pytest.raises(ValueError, match="question must not be blank"):
        await service.create_task(question="   ")

    assert queue.enqueued_task_ids == []
    assert event_repository.events == []


@pytest.mark.anyio
async def test_get_task_returns_an_existing_task() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=queue,
    )
    task = ResearchTask.create(question="调研 Celery 的任务重试机制")
    await repository.add(task)

    found_task = await service.get_task(task.id)

    assert found_task == task


@pytest.mark.anyio
async def test_get_task_returns_none_for_unknown_id() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=queue,
    )

    found_task = await service.get_task(uuid4())

    assert found_task is None


@pytest.mark.anyio
async def test_cancel_task_requests_cancellation_and_persists_it() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
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
    assert [
        (
            event.sequence,
            event.event_type,
            event.payload,
        )
        for event in event_repository.events
    ] == [
        (
            1,
            TaskEventType.CANCEL_REQUESTED,
            {"status": "cancel_requested"},
        ),
    ]
    second_cancellation_request = await service.cancel_task(task.id)

    assert second_cancellation_request is not None
    assert second_cancellation_request.status is TaskStatus.CANCEL_REQUESTED
    assert len(event_repository.events) == 1


@pytest.mark.anyio
async def test_cancel_task_returns_none_for_unknown_id() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    queue = FakeTaskQueue()
    service = TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=queue,
    )

    task_after_cancel_request = await service.cancel_task(uuid4())

    assert task_after_cancel_request is None
    assert queue.enqueued_task_ids == []
