from uuid import uuid4

import pytest

from evidenceforge.domain.events import TaskEventType
from evidenceforge.testing import FakeTaskEventRepository


@pytest.mark.anyio
async def test_list_by_task_id_returns_only_task_events_in_sequence_order() -> None:
    repository = FakeTaskEventRepository()
    task_id = uuid4()
    other_task_id = uuid4()

    await repository.append(
        task_id=other_task_id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )
    await repository.append(
        task_id=task_id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )
    await repository.append(
        task_id=task_id,
        event_type=TaskEventType.RUNNING,
        payload={"status": "running"},
    )

    events = await repository.list_by_task_id(task_id)

    assert [event.sequence for event in events] == [1, 2]
    assert [event.event_type for event in events] == [
        TaskEventType.CREATED,
        TaskEventType.RUNNING,
    ]
    assert all(event.task_id == task_id for event in events)