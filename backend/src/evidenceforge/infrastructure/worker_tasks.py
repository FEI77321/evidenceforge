import asyncio
from uuid import UUID

from celery.utils.log import get_task_logger

from evidenceforge.application.research_task_processor import (
    ResearchTaskProcessor,
)
from evidenceforge.infrastructure.celery_app import celery_app
from evidenceforge.infrastructure.database import (
    async_engine,
    async_session_factory,
)
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)
from evidenceforge.infrastructure.stub_research_executor import (
    StubResearchExecutor,
)


logger = get_task_logger(__name__)


@celery_app.task(name="evidenceforge.run_research_task")
def run_research_task(task_id: str) -> str:
    """由 Celery Worker 在后台执行一条调研任务。"""

    return asyncio.run(_process_research_task(task_id))


async def _process_research_task(task_id: str) -> str:
    """准备基础设施资源并调用任务处理服务。"""

    repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )
    executor = StubResearchExecutor()

    processor = ResearchTaskProcessor(
        repository=repository,
        executor=executor,
    )

    try:
        status = await processor.process(UUID(task_id))
        if status is None:
            logger.warning("research task %s does not exist", task_id)
            return "missing"

        logger.info(
            "research task %s finished with status %s",
            task_id,
            status.value,
        )

        return status.value
    finally:
        await async_engine.dispose()