from collections.abc import Mapping
from uuid import UUID

from evidenceforge.domain.events import TaskEvent, TaskEventType
from evidenceforge.domain.sources import SourceSnapshot
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


class FakeSourceSnapshotRepository:
    """仅供测试使用的内存来源快照仓储。"""

    def __init__(self) -> None:
        self._snapshots: list[SourceSnapshot] = []

    async def add(self, snapshot: SourceSnapshot) -> None:
        """追加保存一条来源快照。"""

        self._snapshots.append(snapshot)

    async def list_by_task_id(
        self,
        task_id: UUID,
    ) -> list[SourceSnapshot]:
        """返回指定任务的全部来源快照。"""

        return sorted(
            (snapshot for snapshot in self._snapshots if snapshot.task_id == task_id),
            key=lambda snapshot: snapshot.captured_at,
        )

class FakeTaskEventRepository:
    """仅供测试使用的内存任务事件仓储。"""

    def __init__(self) -> None:
        self.events: list[TaskEvent] = []

    async def append(
        self,
        *,
        task_id: UUID,
        event_type: TaskEventType,
        stage: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> TaskEvent:
        """按任务维度分配连续序号，并追加一条事件。"""

        sequence = 1 + sum(
            event.task_id == task_id
            for event in self.events
        )
        event = TaskEvent.create(
            task_id=task_id,
            sequence=sequence,
            event_type=event_type,
            stage=stage,
            payload=payload,
        )
        self.events.append(event)

        return event

    async def list_by_task_id(
        self,
        task_id: UUID,
    ) -> list[TaskEvent]:
        """返回指定任务的全部事件，按 sequence 升序排列。"""

        return sorted(
            (
                event
                for event in self.events
                if event.task_id == task_id
            ),
            key=lambda event: event.sequence,
        )


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
