from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from evidenceforge.domain.tasks import ResearchTask, TaskStatus
from evidenceforge.infrastructure.persistence.models import ResearchTaskRecord


class PostgreSQLTaskRepository:
    """使用 PostgreSQL 保存和读取调研任务。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def add(self, task: ResearchTask) -> None:
        """保存一条新建任务。"""

        record = self._to_record(task)

        async with self._session_factory() as session:
            session.add(record)
            await session.commit()

    async def get(self, task_id: UUID) -> ResearchTask | None:
        """按任务 ID 查询任务；不存在时返回 None。"""

        async with self._session_factory() as session:
            record = await session.get(ResearchTaskRecord, task_id)

        if record is None:
            return None

        return self._to_task(record)

    async def update(self, task: ResearchTask) -> None:
        """保存已有任务的最新字段。"""

        async with self._session_factory() as session:
            record = await session.get(ResearchTaskRecord, task.id)
            if record is None:
                raise KeyError(f"task {task.id} does not exist")

            record.question = task.question
            record.status = task.status.value

            await session.commit()

    @staticmethod
    def _to_record(task: ResearchTask) -> ResearchTaskRecord:
        """将领域实体转换为待持久化的数据库记录。"""

        return ResearchTaskRecord(
            id=task.id,
            question=task.question,
            status=task.status.value,
        )

    @staticmethod
    def _to_task(record: ResearchTaskRecord) -> ResearchTask:
        """将数据库记录还原为领域实体。"""

        return ResearchTask.restore(
            task_id=record.id,
            question=record.question,
            status=TaskStatus(record.status),
        )
