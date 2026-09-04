from pathlib import Path
from uuid import UUID

import pytest

from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.infrastructure.fixture_research_executor import (
    FixtureResearchExecutor,
)
from evidenceforge.testing import FakeSourceSnapshotRepository

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "research_sources"
    / "fastapi_background_tasks.md"
)


@pytest.mark.anyio
async def test_load_content_reads_the_fixed_research_source() -> None:
    executor = FixtureResearchExecutor(
        fixture_path=FIXTURE_PATH,
        snapshot_repository=FakeSourceSnapshotRepository(),
    )

    content = await executor.load_content()

    assert "FastAPI BackgroundTasks" in content
    assert "Celery workers can run outside the FastAPI web process." in content


@pytest.mark.anyio
async def test_load_content_raises_when_the_fixture_is_missing(
    tmp_path: Path,
) -> None:
    executor = FixtureResearchExecutor(
        fixture_path=tmp_path / "missing.md",
        snapshot_repository=FakeSourceSnapshotRepository(),
    )

    with pytest.raises(FileNotFoundError):
        await executor.load_content()

@pytest.mark.anyio
async def test_execute_stores_a_snapshot_for_the_research_task() -> None:
    repository = FakeSourceSnapshotRepository()
    executor = FixtureResearchExecutor(
        fixture_path=FIXTURE_PATH,
        snapshot_repository=repository,
    )
    task = ResearchTask.create(
        question="FastAPI BackgroundTasks 何时适合使用？",
        task_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    )

    await executor.execute(task)

    snapshots = await repository.list_by_task_id(task.id)

    assert len(snapshots) == 1

    snapshot = snapshots[0]
    assert snapshot.task_id == task.id
    assert snapshot.source_uri == "fixture://fastapi_background_tasks.md"
    assert snapshot.source_kind == "fixture"
    assert "FastAPI BackgroundTasks" in snapshot.raw_content
    assert len(snapshot.content_hash) == 64