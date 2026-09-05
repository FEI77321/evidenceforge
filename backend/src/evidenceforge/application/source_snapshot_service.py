from uuid import UUID

from evidenceforge.domain.ports import (
    SourceSnapshotRepository,
    TaskRepository,
)
from evidenceforge.domain.sources import SourceSnapshot


class SourceSnapshotService:
    """组织来源快照读取用例。"""

    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        snapshot_repository: SourceSnapshotRepository,
    ) -> None:
        self._task_repository = task_repository
        self._snapshot_repository = snapshot_repository

    async def list_sources(
        self,
        task_id: UUID,
    ) -> list[SourceSnapshot] | None:
        """读取指定任务的来源快照；任务不存在时返回 None。"""

        task = await self._task_repository.get(task_id)
        if task is None:
            return None

        return await self._snapshot_repository.list_by_task_id(task_id)
