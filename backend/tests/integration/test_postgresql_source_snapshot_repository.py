from datetime import UTC, datetime

import pytest

from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.infrastructure.database import async_session_factory
from evidenceforge.infrastructure.persistence.source_snapshot_repository import (
    PostgreSQLSourceSnapshotRepository,
)
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)


@pytest.mark.anyio
async def test_add_then_list_by_task_id_returns_persisted_snapshots() -> None:
    task_repository = PostgreSQLTaskRepository(async_session_factory)
    snapshot_repository = PostgreSQLSourceSnapshotRepository(
        async_session_factory,
    )
    task = ResearchTask.create(
        question="调研 FastAPI BackgroundTasks 的适用边界",
    )
    snapshot = SourceSnapshot.create(
        task_id=task.id,
        source_uri="fixture://fastapi_background_tasks.md",
        source_kind="fixture",
        raw_content="FastAPI BackgroundTasks are useful for small tasks.",
        captured_at=datetime(2026, 9, 4, 6, 0, tzinfo=UTC),
    )

    await task_repository.add(task)
    await snapshot_repository.add(snapshot)

    snapshots = await snapshot_repository.list_by_task_id(task.id)

    assert snapshots == [snapshot]


@pytest.mark.anyio
async def test_list_by_task_id_filters_other_tasks_and_orders_by_capture_time() -> None:
    task_repository = PostgreSQLTaskRepository(async_session_factory)
    snapshot_repository = PostgreSQLSourceSnapshotRepository(
        async_session_factory,
    )
    task = ResearchTask.create(
        question="调研任务自己的来源历史",
    )
    other_task = ResearchTask.create(
        question="另一项任务不应混入来源历史",
    )
    first_snapshot = SourceSnapshot.create(
        task_id=task.id,
        source_uri="fixture://first.md",
        source_kind="fixture",
        raw_content="first source content",
        captured_at=datetime(2026, 9, 4, 6, 0, tzinfo=UTC),
    )
    second_snapshot = SourceSnapshot.create(
        task_id=task.id,
        source_uri="fixture://second.md",
        source_kind="fixture",
        raw_content="second source content",
        captured_at=datetime(2026, 9, 4, 7, 0, tzinfo=UTC),
    )
    other_snapshot = SourceSnapshot.create(
        task_id=other_task.id,
        source_uri="fixture://other.md",
        source_kind="fixture",
        raw_content="other task source content",
        captured_at=datetime(2026, 9, 4, 8, 0, tzinfo=UTC),
    )

    await task_repository.add(task)
    await task_repository.add(other_task)
    await snapshot_repository.add(first_snapshot)
    await snapshot_repository.add(second_snapshot)
    await snapshot_repository.add(other_snapshot)

    snapshots = await snapshot_repository.list_by_task_id(task.id)

    assert snapshots == [first_snapshot, second_snapshot]