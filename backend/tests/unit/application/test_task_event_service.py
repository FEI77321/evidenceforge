from uuid import uuid4

import pytest

from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.testing import (
    FakeTaskEventRepository,
    FakeTaskRepository,
)


@pytest.mark.anyio
async def test_list_events_returns_events_for_an_existing_task() -> None:
    task_repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    service = TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )
    task = ResearchTask.create(
        question="调研任务审计事件如何用于状态时间线",
    )

    await task_repository.add(task)
    created_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )
    running_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.RUNNING,
        payload={"status": "running"},
    )

    events = await service.list_events(task.id)

    assert events == [created_event, running_event]


@pytest.mark.anyio
async def test_list_events_returns_an_empty_list_for_an_existing_task_without_events() -> (
    None
):
    task_repository = FakeTaskRepository()
    service = TaskEventService(
        task_repository=task_repository,
        event_repository=FakeTaskEventRepository(),
    )
    task = ResearchTask.create(
        question="尚未产生审计事件的任务",
    )

    await task_repository.add(task)

    events = await service.list_events(task.id)

    assert events == []


@pytest.mark.anyio
async def test_list_events_returns_none_when_the_task_does_not_exist() -> None:
    service = TaskEventService(
        task_repository=FakeTaskRepository(),
        event_repository=FakeTaskEventRepository(),
    )

    events = await service.list_events(uuid4())

    assert events is None