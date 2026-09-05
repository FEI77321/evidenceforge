from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from evidenceforge.domain.events import TaskEvent, TaskEventType
from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.domain.tasks import ResearchTask


class TaskRepository(Protocol):
    """调研任务持久化能力的抽象契约。"""

    async def add(self, task: ResearchTask) -> None:
        """保存一条新建任务。"""

    async def get(self, task_id: UUID) -> ResearchTask | None:
        """按任务 ID 查询任务；不存在时返回 None。"""

    async def update(self, task: ResearchTask) -> None:
        """保存任务状态等字段的后续变更。"""


class SourceSnapshotRepository(Protocol):
    """来源快照追加保存与按任务查询的抽象契约。"""

    async def add(self, snapshot: SourceSnapshot) -> None:
        """追加保存一条不可变来源快照。"""

    async def list_by_task_id(
        self,
        task_id: UUID,
    ) -> list[SourceSnapshot]:
        """返回某调研任务对应的全部来源快照。"""


class TaskEventRepository(Protocol):
    """任务审计事件的追加式持久化能力。"""

    async def append(
        self,
        *,
        task_id: UUID,
        event_type: TaskEventType,
        stage: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> TaskEvent:
        """为任务追加一条事件，并返回带连续序号的事件。"""


class TaskQueue(Protocol):
    """调研任务投递到后台执行器的抽象契约。"""

    async def enqueue(self, task_id: UUID) -> None:
        """投递指定任务，供后台 Worker 异步处理。"""


class ResearchExecutor(Protocol):
    """执行一条调研任务中的实际耗时工作。"""

    async def execute(self, task: ResearchTask) -> None:
        """执行调研工作；执行失败时抛出异常。"""