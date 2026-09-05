from uuid import uuid4

import pytest

from evidenceforge.application.research_task_processor import (
    ResearchTaskProcessor,
)
from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.testing import (
    FakeResearchExecutor,
    FakeTaskEventRepository,
    FakeTaskRepository,
)


@pytest.mark.anyio
async def test_process_completes_a_queued_task() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    executor = FakeResearchExecutor()
    task = ResearchTask.create(question="调研 Celery Worker 的执行过程")
    await repository.add(task)
    processor = ResearchTaskProcessor(
        repository=repository,
        executor=executor,
        event_repository=event_repository,
    )

    status = await processor.process(task.id)
    stored_task = await repository.get(task.id)

    assert status is TaskStatus.COMPLETED
    assert stored_task is not None
    assert stored_task.status is TaskStatus.COMPLETED
    assert executor.executed_task_ids == [task.id]
    assert [
        (event.sequence, event.event_type, event.payload)
        for event in event_repository.events
    ] == [
        (1, TaskEventType.RUNNING, {"status": "running"}),
        (2, TaskEventType.COMPLETED, {"status": "completed"}),
    ]


@pytest.mark.anyio
async def test_process_cancels_a_task_with_a_pending_cancellation_request() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    executor = FakeResearchExecutor()
    task = ResearchTask.create(question="调研取消中的后台任务")
    task.request_cancellation()
    await repository.add(task)
    await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.CANCEL_REQUESTED,
        payload={"status": "cancel_requested"},
    )
    processor = ResearchTaskProcessor(
        repository=repository,
        executor=executor,
        event_repository=event_repository,
    )

    status = await processor.process(task.id)
    stored_task = await repository.get(task.id)

    assert status is TaskStatus.CANCELED
    assert stored_task is not None
    assert stored_task.status is TaskStatus.CANCELED
    assert executor.executed_task_ids == []
    assert [
        (event.sequence, event.event_type, event.payload)
        for event in event_repository.events
    ] == [
        (1, TaskEventType.CANCEL_REQUESTED, {"status": "cancel_requested"}),
        (2, TaskEventType.CANCELED, {"status": "canceled"}),
    ]


@pytest.mark.anyio
async def test_process_keeps_a_terminal_task_unchanged() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    executor = FakeResearchExecutor()
    task = ResearchTask.create(question="调研已经完成的任务")
    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)
    await repository.add(task)
    processor = ResearchTaskProcessor(
        repository=repository,
        executor=executor,
        event_repository=event_repository,
    )

    status = await processor.process(task.id)
    stored_task = await repository.get(task.id)

    assert status is TaskStatus.COMPLETED
    assert stored_task is not None
    assert stored_task.status is TaskStatus.COMPLETED
    assert executor.executed_task_ids == []
    assert event_repository.events == []


@pytest.mark.anyio
async def test_process_returns_none_for_an_unknown_task() -> None:
    processor = ResearchTaskProcessor(
        repository=FakeTaskRepository(),
        executor=FakeResearchExecutor(),
        event_repository=FakeTaskEventRepository(),
    )

    status = await processor.process(uuid4())

    assert status is None


@pytest.mark.anyio
async def test_process_marks_a_failed_execution_as_failed() -> None:
    repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    executor = FakeResearchExecutor(
        error=RuntimeError("research source is unavailable"),
    )
    task = ResearchTask.create(question="调研失效来源的处理方式")
    await repository.add(task)
    processor = ResearchTaskProcessor(
        repository=repository,
        executor=executor,
        event_repository=event_repository,
    )

    with pytest.raises(
        RuntimeError,
        match="research source is unavailable",
    ):
        await processor.process(task.id)

    stored_task = await repository.get(task.id)

    assert stored_task is not None
    assert stored_task.status is TaskStatus.FAILED
    assert executor.executed_task_ids == [task.id]
    assert [
        (event.sequence, event.event_type, event.payload)
        for event in event_repository.events
    ] == [
        (1, TaskEventType.RUNNING, {"status": "running"}),
        (2, TaskEventType.FAILED, {"status": "failed"}),
    ]
