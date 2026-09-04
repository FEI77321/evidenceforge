import asyncio
from pathlib import Path

from celery.utils.log import get_task_logger

from evidenceforge.domain.ports import SourceSnapshotRepository
from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.domain.tasks import ResearchTask

logger = get_task_logger(__name__)


class FixtureResearchExecutor:
    """读取固定本地资料并保存来源快照的开发期执行器。"""

    def __init__(
        self,
        fixture_path: Path,
        snapshot_repository: SourceSnapshotRepository,
    ) -> None:
        self._fixture_path = fixture_path
        self._snapshot_repository = snapshot_repository

    async def load_content(self) -> str:
        """以 UTF-8 读取固定资料的完整内容。"""

        return await asyncio.to_thread(
            self._fixture_path.read_text,
            encoding="utf-8",
        )

    async def execute(self, task: ResearchTask) -> None:
        """读取固定资料，并为本次任务追加来源快照。"""

        content = await self.load_content()

        snapshot = SourceSnapshot.create(
            task_id=task.id,
            source_uri=f"fixture://{self._fixture_path.name}",
            source_kind="fixture",
            raw_content=content,
        )
        await self._snapshot_repository.add(snapshot)

        logger.info(
            "research task %s stored fixture snapshot %s from %s (%d characters)",
            task.id,
            snapshot.id,
            self._fixture_path.name,
            len(content),
        )