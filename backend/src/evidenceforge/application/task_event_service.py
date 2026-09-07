from uuid import UUID

from evidenceforge.domain.events import TaskEvent
from evidenceforge.domain.ports import (
    TaskEventRepository,
    TaskRepository,
)


class TaskEventService:
    """组织任务审计事件读取用例。"""

    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        event_repository: TaskEventRepository,
    ) -> None:
        self._task_repository = task_repository
        self._event_repository = event_repository

    async def list_events(
        self,
        task_id: UUID,
    ) -> list[TaskEvent] | None:
        """读取任务事件；任务不存在时返回 None。"""

        task = await self._task_repository.get(task_id)
        if task is None:
            return None

        return await self._event_repository.list_by_task_id(task_id)