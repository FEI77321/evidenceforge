from uuid import UUID

from evidenceforge.domain.ports import TaskQueue, TaskRepository
from evidenceforge.domain.tasks import ResearchTask


class TaskService:
    """组织调研任务相关应用用例。"""

    def __init__(
        self,
        repository: TaskRepository,
        queue: TaskQueue,
    ) -> None:
        self._repository = repository
        self._queue = queue

    async def create_task(self, question: str) -> ResearchTask:
        """创建、保存并投递一条调研任务。"""

        task = ResearchTask.create(question=question)

        await self._repository.add(task)
        await self._queue.enqueue(task.id)

        return task

    async def get_task(self, task_id: UUID) -> ResearchTask | None:
        """按任务 ID 查询任务。"""

        return await self._repository.get(task_id)

    async def cancel_task(self, task_id: UUID) -> ResearchTask | None:
        """请求取消任务，并保存发生的状态变化。"""

        task = await self._repository.get(task_id)
        if task is None:
            return None

        cancellation_accepted = task.request_cancellation()
        if cancellation_accepted:
            await self._repository.update(task)

        return task
