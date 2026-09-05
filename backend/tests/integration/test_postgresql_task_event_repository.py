import pytest
from sqlalchemy import select

from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.infrastructure.database import async_session_factory
from evidenceforge.infrastructure.persistence.models import TaskEventRecord
from evidenceforge.infrastructure.persistence.task_event_repository import (
    PostgreSQLTaskEventRepository,
)
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)


@pytest.mark.anyio
async def test_append_persists_task_scoped_ordered_events() -> None:
    task_repository = PostgreSQLTaskRepository(async_session_factory)
    event_repository = PostgreSQLTaskEventRepository(
        async_session_factory,
    )
    first_task = ResearchTask.create(
        question="调研第一项任务的事件顺序",
    )
    second_task = ResearchTask.create(
        question="调研第二项任务的事件顺序",
    )

    await task_repository.add(first_task)
    await task_repository.add(second_task)

    created_event = await event_repository.append(
        task_id=first_task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )
    running_event = await event_repository.append(
        task_id=first_task.id,
        event_type=TaskEventType.RUNNING,
        payload={"status": "running"},
    )
    other_task_event = await event_repository.append(
        task_id=second_task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )

    assert created_event.sequence == 1
    assert running_event.sequence == 2
    assert other_task_event.sequence == 1

    async with async_session_factory() as session:
        first_task_records = (
            await session.scalars(
                select(TaskEventRecord)
                .where(TaskEventRecord.task_id == first_task.id)
                .order_by(TaskEventRecord.sequence.asc())
            )
        ).all()

    assert [
        (
            record.sequence,
            record.event_type,
            record.stage,
            record.payload,
        )
        for record in first_task_records
    ] == [
        (1, "created", None, {"status": "queued"}),
        (2, "running", None, {"status": "running"}),
    ]
