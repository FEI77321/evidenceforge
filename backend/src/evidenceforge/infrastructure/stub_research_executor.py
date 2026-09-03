import asyncio

from celery.utils.log import get_task_logger

from evidenceforge.domain.tasks import ResearchTask

logger = get_task_logger(__name__)


class StubResearchExecutor:
    """当前阶段的临时调研执行器。"""

    async def execute(self, task: ResearchTask) -> None:
        """模拟一次成功的调研执行。"""

        logger.info(
            "research task %s is executing stub research work",
            task.id,
        )

        await asyncio.sleep(0)