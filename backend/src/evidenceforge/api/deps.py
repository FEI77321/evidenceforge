from evidenceforge.application.task_service import TaskService
from evidenceforge.infrastructure.database import async_session_factory
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)
from evidenceforge.testing import FakeTaskQueue

_queue = FakeTaskQueue()


def get_task_service() -> TaskService:
    """为 API Router 提供真实持久化的任务应用服务。"""

    repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )

    return TaskService(
        repository=repository,
        queue=_queue,
    )
