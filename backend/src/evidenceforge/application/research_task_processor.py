from uuid import UUID

from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.ports import (
    ResearchExecutor,
    TaskEventRepository,
    TaskRepository,
)
from evidenceforge.domain.tasks import ResearchTask, TaskStatus


class ResearchTaskProcessor:
    """处理后台调研任务的状态流转。"""

    def __init__(
        self,
        repository: TaskRepository,
        executor: ResearchExecutor,
        event_repository: TaskEventRepository,
    ) -> None:
        self._repository = repository
        self._executor = executor
        self._event_repository = event_repository

    async def process(self, task_id: UUID) -> TaskStatus | None:
        """处理一条任务，并返回处理后的状态。"""

        task = await self._repository.get(task_id)
        if task is None:
            return None

        # Worker 真正开始执行前，已经收到取消请求。
        if task.status is TaskStatus.CANCEL_REQUESTED:
            task.transition_to(TaskStatus.CANCELED)
            await self._repository.update(task)
            await self._append_status_event(
                task,
                TaskEventType.CANCELED,
            )
            return task.status

        # 已完成、已失败、已取消等终态任务不应重复执行或重复写事件。
        if task.status is not TaskStatus.QUEUED:
            return task.status

        # queued -> running
        task.transition_to(TaskStatus.RUNNING)
        await self._repository.update(task)
        await self._append_status_event(
            task,
            TaskEventType.RUNNING,
        )

        try:
            await self._executor.execute(task)
        except Exception:
            current_task = await self._repository.get(task.id)

            if current_task is None:
                raise

            # 执行期间有人请求取消：优先完成取消，不把任务标记为失败。
            if current_task.status is TaskStatus.CANCEL_REQUESTED:
                current_task.transition_to(TaskStatus.CANCELED)
                await self._repository.update(current_task)
                await self._append_status_event(
                    current_task,
                    TaskEventType.CANCELED,
                )
                return current_task.status

            # 真正的执行异常：running -> failed，然后仍把原异常抛回给 Celery。
            if current_task.status is TaskStatus.RUNNING:
                current_task.transition_to(TaskStatus.FAILED)
                await self._repository.update(current_task)
                await self._append_status_event(
                    current_task,
                    TaskEventType.FAILED,
                )

            raise

        current_task = await self._repository.get(task.id)
        if current_task is None:
            return None

        # 执行成功后，再读一次任务状态，处理执行期间可能发生的取消请求。
        if current_task.status is TaskStatus.CANCEL_REQUESTED:
            current_task.transition_to(TaskStatus.CANCELED)
            event_type = TaskEventType.CANCELED
        elif current_task.status is TaskStatus.RUNNING:
            current_task.transition_to(TaskStatus.COMPLETED)
            event_type = TaskEventType.COMPLETED
        else:
            return current_task.status

        await self._repository.update(current_task)
        await self._append_status_event(current_task, event_type)

        return current_task.status

    async def _append_status_event(
        self,
        task: ResearchTask,
        event_type: TaskEventType,
    ) -> None:
        """为已成功保存的任务状态变化追加审计事件。"""

        await self._event_repository.append(
            task_id=task.id,
            event_type=event_type,
            payload={"status": task.status.value},
        )