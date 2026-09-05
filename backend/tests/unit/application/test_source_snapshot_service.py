from datetime import UTC, datetime
from uuid import uuid4

import pytest

from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.testing import (
    FakeSourceSnapshotRepository,
    FakeTaskRepository,
)


@pytest.mark.anyio
async def test_list_sources_returns_snapshots_for_an_existing_task() -> None:
    task_repository = FakeTaskRepository()
    snapshot_repository = FakeSourceSnapshotRepository()
    service = SourceSnapshotService(
        task_repository=task_repository,
        snapshot_repository=snapshot_repository,
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

    sources = await service.list_sources(task.id)

    assert sources == [snapshot]


@pytest.mark.anyio
async def test_list_sources_returns_an_empty_list_for_an_existing_task_without_sources() -> (
    None
):
    task_repository = FakeTaskRepository()
    snapshot_repository = FakeSourceSnapshotRepository()
    service = SourceSnapshotService(
        task_repository=task_repository,
        snapshot_repository=snapshot_repository,
    )
    task = ResearchTask.create(
        question="尚未开始执行的调研任务",
    )

    await task_repository.add(task)

    sources = await service.list_sources(task.id)

    assert sources == []


@pytest.mark.anyio
async def test_list_sources_returns_none_when_the_task_does_not_exist() -> None:
    service = SourceSnapshotService(
        task_repository=FakeTaskRepository(),
        snapshot_repository=FakeSourceSnapshotRepository(),
    )

    sources = await service.list_sources(uuid4())

    assert sources is None
