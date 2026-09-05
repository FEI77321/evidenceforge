from datetime import UTC, datetime
from uuid import UUID

import pytest

from evidenceforge.domain.events import (
    TaskEvent,
    TaskEventType,
)

TASK_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OCCURRED_AT = datetime(2026, 9, 5, 6, 0, tzinfo=UTC)


def test_create_task_event_preserves_its_audit_fields() -> None:
    event = TaskEvent.create(
        task_id=TASK_ID,
        sequence=1,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
        occurred_at=OCCURRED_AT,
    )

    assert event.task_id == TASK_ID
    assert event.sequence == 1
    assert event.event_type is TaskEventType.CREATED
    assert event.stage is None
    assert event.payload == {"status": "queued"}
    assert event.occurred_at == OCCURRED_AT


def test_create_task_event_rejects_a_non_positive_sequence() -> None:
    with pytest.raises(ValueError, match="sequence must be positive"):
        TaskEvent.create(
            task_id=TASK_ID,
            sequence=0,
            event_type=TaskEventType.CREATED,
        )


def test_create_task_event_rejects_a_blank_stage() -> None:
    with pytest.raises(ValueError, match="stage must not be blank"):
        TaskEvent.create(
            task_id=TASK_ID,
            sequence=1,
            event_type=TaskEventType.RUNNING,
            stage="   ",
        )