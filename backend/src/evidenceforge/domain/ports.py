from typing import Protocol
from uuid import UUID

from evidenceforge.domain.tasks import ResearchTask


class TaskRepository(Protocol):
    """调研任务持久化能力的抽象契约。"""

    async def add(self, task: ResearchTask) -> None:
        """保存一条新建任务。"""

    async def get(self, task_id: UUID) -> ResearchTask | None:
        """按任务 ID 查询任务；不存在时返回 None。"""

    async def update(self, task: ResearchTask) -> None:
        """保存任务状态等字段的后续变更。"""


class TaskQueue(Protocol):
    """调研任务投递到后台执行器的抽象契约。"""

    async def enqueue(self, task_id: UUID) -> None:
        """投递指定任务，供后台 Worker 异步处理。"""
