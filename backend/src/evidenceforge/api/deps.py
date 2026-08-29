from evidenceforge.application.task_service import TaskService
from evidenceforge.testing import FakeTaskQueue, FakeTaskRepository

_repository = FakeTaskRepository()
_queue = FakeTaskQueue()
_task_service = TaskService(
    repository=_repository,
    queue=_queue,
)


def get_task_service() -> TaskService:
    """为 API Router 提供任务应用服务。"""

    return _task_service
