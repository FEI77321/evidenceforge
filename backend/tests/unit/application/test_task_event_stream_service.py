from uuid import uuid4

import pytest

from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.application.task_event_stream_service import (
    TaskEventStreamService,
)
from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.testing import (
    FakeTaskEventRepository,
    FakeTaskRepository,
)


@pytest.mark.anyio
async def test_stream_events_replays_existing_events_then_emits_new_events() -> (
    None
):
    task_repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    task_event_service = TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )
    stream_service = TaskEventStreamService(
        task_event_service=task_event_service,
        poll_interval_seconds=0.01,
    )
    task = ResearchTask.create(
        question="验证事件流的回放与新增事件推送",
    )

    await task_repository.add(task)
    created_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )

    event_stream = stream_service.stream_events(
        task.id,
        initial_events=[created_event],
    )

    first_event = await anext(event_stream)

    assert first_event == created_event

    running_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.RUNNING,
        payload={"status": "running"},
    )

    second_event = await anext(event_stream)

    assert second_event == running_event

    await event_stream.aclose()


@pytest.mark.anyio
async def test_stream_events_emits_an_event_added_after_the_stream_opens() -> None:
    task_repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    task_event_service = TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )
    stream_service = TaskEventStreamService(
        task_event_service=task_event_service,
        poll_interval_seconds=0.01,
    )
    task = ResearchTask.create(
        question="验证空事件流后续能观察到新事件",
    )

    await task_repository.add(task)

    event_stream = stream_service.stream_events(
        task.id,
        initial_events=[],
    )

    created_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )

    first_event = await anext(event_stream)

    assert first_event == created_event

    await event_stream.aclose()


@pytest.mark.anyio
async def test_stream_events_stops_when_the_task_does_not_exist() -> None:
    task_event_service = TaskEventService(
        task_repository=FakeTaskRepository(),
        event_repository=FakeTaskEventRepository(),
    )
    stream_service = TaskEventStreamService(
        task_event_service=task_event_service,
        poll_interval_seconds=0.01,
    )

    event_stream = stream_service.stream_events(
        uuid4(),
        initial_events=[],
    )

    with pytest.raises(StopAsyncIteration):
        await anext(event_stream)
