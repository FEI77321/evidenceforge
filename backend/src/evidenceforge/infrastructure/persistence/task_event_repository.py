from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from evidenceforge.domain.events import TaskEvent, TaskEventType
from evidenceforge.infrastructure.persistence.models import (
    ResearchTaskRecord,
    TaskEventRecord,
)


class PostgreSQLTaskEventRepository:
    """使用 PostgreSQL 追加保存任务审计事件。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def append(
        self,
        *,
        task_id: UUID,
        event_type: TaskEventType,
        stage: str | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> TaskEvent:
        """为一个已存在任务追加下一条连续序号事件。"""
        async with self._session_factory() as session:
            async with session.begin():
                task_record_id = await session.scalar(
                    select(ResearchTaskRecord.id)
                    .where(ResearchTaskRecord.id == task_id)
                    .with_for_update()
                )
                if task_record_id is None:
                    raise KeyError(f"task {task_id} does not exist")

                next_sequence = await session.scalar(
                    select(
                        func.coalesce(
                            func.max(TaskEventRecord.sequence),
                            0,
                        )
                        + 1
                    ).where(TaskEventRecord.task_id == task_id)
                )

                event = TaskEvent.create(
                    task_id=task_id,
                    sequence=int(next_sequence),
                    event_type=event_type,
                    stage=stage,
                    payload=payload,
                )
                session.add(
                    TaskEventRecord(
                        task_id=event.task_id,
                        sequence=event.sequence,
                        event_type=event.event_type.value,
                        stage=event.stage,
                        payload=dict(event.payload),
                        occurred_at=event.occurred_at,
                    )
                )

            return event

    async def list_by_task_id(
        self,
        task_id: UUID,
    ) -> list[TaskEvent]:
        """读取指定任务的全部事件，并按 sequence 升序排列。"""

        statement = (
            select(TaskEventRecord)
            .where(TaskEventRecord.task_id == task_id)
            .order_by(TaskEventRecord.sequence.asc())
        )

        async with self._session_factory() as session:
            records = (await session.scalars(statement)).all()

        return [
            TaskEvent.create(
                task_id=record.task_id,
                sequence=record.sequence,
                event_type=TaskEventType(record.event_type),
                stage=record.stage,
                payload=record.payload,
                occurred_at=record.occurred_at,
            )
            for record in records
        ]
