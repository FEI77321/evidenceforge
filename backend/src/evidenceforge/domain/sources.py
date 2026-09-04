from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SourceSnapshot:
    """一次调研任务在某个时刻保存的不可变来源快照。"""

    id: UUID
    task_id: UUID
    source_uri: str
    source_kind: str
    raw_content: str
    content_hash: str
    captured_at: datetime

    @classmethod
    def create(
        cls,
        *,
        task_id: UUID,
        source_uri: str,
        source_kind: str,
        raw_content: str,
        snapshot_id: UUID | None = None,
        captured_at: datetime | None = None,
    ) -> "SourceSnapshot":
        """根据一次实际读取的来源内容创建快照。"""

        normalized_source_uri = source_uri.strip()
        normalized_source_kind = source_kind.strip()

        if not normalized_source_uri:
            raise ValueError("source_uri must not be blank")

        if not normalized_source_kind:
            raise ValueError("source_kind must not be blank")

        return cls(
            id=snapshot_id or uuid4(),
            task_id=task_id,
            source_uri=normalized_source_uri,
            source_kind=normalized_source_kind,
            raw_content=raw_content,
            content_hash=sha256(raw_content.encode("utf-8")).hexdigest(),
            captured_at=captured_at or datetime.now(UTC),
        )

    @classmethod
    def restore(
        cls,
        *,
        snapshot_id: UUID,
        task_id: UUID,
        source_uri: str,
        source_kind: str,
        raw_content: str,
        content_hash: str,
        captured_at: datetime,
    ) -> "SourceSnapshot":
        """从可信持久化数据还原一条既有来源快照。"""

        return cls(
            id=snapshot_id,
            task_id=task_id,
            source_uri=source_uri,
            source_kind=source_kind,
            raw_content=raw_content,
            content_hash=content_hash,
            captured_at=captured_at,
        )

