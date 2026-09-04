import asyncio
from pathlib import Path

from celery.utils.log import get_task_logger

from evidenceforge.domain.tasks import ResearchTask

logger = get_task_logger(__name__)


class FixtureResearchExecutor:
    """读取固定本地资料的开发期调研执行器。"""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    async def load_content(self) -> str:
        """以 UTF-8 读取固定资料的完整内容。"""

        return await asyncio.to_thread(
            self._fixture_path.read_text,
            encoding="utf-8",
        )

    async def execute(self, task: ResearchTask) -> None:
        """读取固定资料，并记录本次处理的摘要信息。"""

        content = await self.load_content()

        logger.info(
            "research task %s loaded fixture %s (%d characters)",
            task.id,
            self._fixture_path.name,
            len(content),
        )