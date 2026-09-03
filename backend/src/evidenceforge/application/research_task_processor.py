from uuid import UUID

from evidenceforge.domain.ports import ResearchExecutor, TaskRepository
from evidenceforge.domain.tasks import TaskStatus


class ResearchTaskProcessor:
    """处理后台调研任务的状态流转。"""

    def __init__(
        self,
        repository: TaskRepository,
        executor: ResearchExecutor,
    ) -> None:
        self._repository = repository
        self._executor = executor

    async def process(self, task_id: UUID) -> TaskStatus | None:
        """处理一条任务，并返回处理后的状态。"""

        task = await self._repository.get(task_id)
        if task is None:
            return None

        if task.status is TaskStatus.CANCEL_REQUESTED:
            task.transition_to(TaskStatus.CANCELED)
            await self._repository.update(task)
            return task.status

        if task.status is not TaskStatus.QUEUED:
            return task.status

        task.transition_to(TaskStatus.RUNNING)
        await self._repository.update(task)

        try:
            await self._executor.execute(task)
        except Exception:
            current_task = await self._repository.get(task.id)

            if current_task is None:
                raise

            if current_task.status is TaskStatus.CANCEL_REQUESTED:
                current_task.transition_to(TaskStatus.CANCELED)
                await self._repository.update(current_task)
                return current_task.status

            if current_task.status is TaskStatus.RUNNING:
                current_task.transition_to(TaskStatus.FAILED)
                await self._repository.update(current_task)

            raise

        current_task = await self._repository.get(task.id)
        if current_task is None:
            return None

        if current_task.status is TaskStatus.CANCEL_REQUESTED:
            current_task.transition_to(TaskStatus.CANCELED)
        elif current_task.status is TaskStatus.RUNNING:
            current_task.transition_to(TaskStatus.COMPLETED)
        else:
            return current_task.status

        await self._repository.update(current_task)

        return current_task.status