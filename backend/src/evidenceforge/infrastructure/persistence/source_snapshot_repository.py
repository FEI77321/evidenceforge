from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.infrastructure.persistence.models import SourceSnapshotRecord


class PostgreSQLSourceSnapshotRepository:
    """使用 PostgreSQL 保存和读取来源快照。"""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def add(self, snapshot: SourceSnapshot) -> None:
        """追加保存一条不可变来源快照。"""

        record = self._to_record(snapshot)

        async with self._session_factory() as session:
            session.add(record)
            await session.commit()

    async def list_by_task_id(
        self,
        task_id: UUID,
    ) -> list[SourceSnapshot]:
        """返回指定任务的来源快照，按抓取时间升序排列。"""

        statement = (
            select(SourceSnapshotRecord)
            .where(SourceSnapshotRecord.task_id == task_id)
            .order_by(SourceSnapshotRecord.captured_at.asc())
        )

        async with self._session_factory() as session:
            records = (await session.scalars(statement)).all()

        return [
            self._to_snapshot(record)
            for record in records
        ]

    @staticmethod
    def _to_record(snapshot: SourceSnapshot) -> SourceSnapshotRecord:
        """将领域快照转换为待持久化的数据库记录。"""

        return SourceSnapshotRecord(
            id=snapshot.id,
            task_id=snapshot.task_id,
            source_uri=snapshot.source_uri,
            source_kind=snapshot.source_kind,
            raw_content=snapshot.raw_content,
            content_hash=snapshot.content_hash,
            captured_at=snapshot.captured_at,
        )

    @staticmethod
    def _to_snapshot(record: SourceSnapshotRecord) -> SourceSnapshot:
        """将数据库记录还原为领域来源快照。"""

        return SourceSnapshot.restore(
            snapshot_id=record.id,
            task_id=record.task_id,
            source_uri=record.source_uri,
            source_kind=record.source_kind,
            raw_content=record.raw_content,
            content_hash=record.content_hash,
            captured_at=record.captured_at,
        )