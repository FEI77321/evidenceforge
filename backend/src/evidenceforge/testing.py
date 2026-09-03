from uuid import UUID

from evidenceforge.domain.tasks import ResearchTask


class FakeTaskRepository:
    """仅供测试使用的内存任务仓储。"""

    def __init__(self) -> None:
        self._tasks: dict[UUID, ResearchTask] = {}

    async def add(self, task: ResearchTask) -> None:
        """保存一条新任务。"""

        self._tasks[task.id] = task

    async def get(self, task_id: UUID) -> ResearchTask | None:
        """按任务 ID 查询任务；不存在时返回 None。"""

        return self._tasks.get(task_id)

    async def update(self, task: ResearchTask) -> None:
        """保存已有任务的最新状态。"""

        self._tasks[task.id] = task


class FakeTaskQueue:
    """仅供测试使用的内存任务队列。"""

    def __init__(self) -> None:
        self.enqueued_task_ids: list[UUID] = []

    async def enqueue(self, task_id: UUID) -> None:
        """记录一条被投递的任务 ID。"""

        self.enqueued_task_ids.append(task_id)

class FakeResearchExecutor:
    """仅供测试使用的调研执行器。"""

    def __init__(self, error: Exception | None = None) -> None:
        self.executed_task_ids: list[UUID] = []
        self._error = error

    async def execute(self, task: ResearchTask) -> None:
        """记录执行过的任务；配置异常时模拟执行失败。"""

        self.executed_task_ids.append(task.id)

        if self._error is not None:
            raise self._error
