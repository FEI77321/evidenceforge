from pathlib import Path

import pytest

from evidenceforge.infrastructure.fixture_research_executor import (
    FixtureResearchExecutor,
)

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
    )

    with pytest.raises(FileNotFoundError):
        await executor.load_content()