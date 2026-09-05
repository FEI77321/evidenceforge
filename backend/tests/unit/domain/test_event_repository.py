from uuid import UUID

import pytest

from evidenceforge.domain.events import TaskEventType
from evidenceforge.testing import FakeTaskEventRepository

FIRST_TASK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SECOND_TASK_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.mark.anyio
async def test_task_event_repository_assigns_sequences_per_task() -> None:
    repository = FakeTaskEventRepository()

    created_event = await repository.append(
        task_id=FIRST_TASK_ID,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )
    running_event = await repository.append(
        task_id=FIRST_TASK_ID,
        event_type=TaskEventType.RUNNING,
        payload={"status": "running"},
    )
    other_task_event = await repository.append(
        task_id=SECOND_TASK_ID,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )

    assert created_event.sequence == 1
    assert running_event.sequence == 2
    assert other_task_event.sequence == 1

    assert repository.events == [
        created_event,
        running_event,
        other_task_event,
    ]


@pytest.mark.anyio
async def test_task_event_repository_preserves_event_metadata() -> None:
    repository = FakeTaskEventRepository()

    event = await repository.append(
        task_id=FIRST_TASK_ID,
        event_type=TaskEventType.FAILED,
        stage="fixture_read",
        payload={
            "status": "failed",
            "error_code": "fixture_not_found",
        },
    )

    assert event.task_id == FIRST_TASK_ID
    assert event.sequence == 1
    assert event.event_type is TaskEventType.FAILED
    assert event.stage == "fixture_read"
    assert event.payload == {
        "status": "failed",
        "error_code": "fixture_not_found",
    }