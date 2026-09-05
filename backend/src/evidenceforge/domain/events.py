from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


class TaskEventType(StrEnum):
    """任务生命周期中可审计的事件类型。"""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELED = "canceled"


@dataclass(frozen=True)
class TaskEvent:
    """一次任务状态变化产生的追加式审计事件。"""

    task_id: UUID
    sequence: int
    event_type: TaskEventType
    stage: str | None
    payload: Mapping[str, object]
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        *,
        task_id: UUID,
        sequence: int,
        event_type: TaskEventType,
        stage: str | None = None,
        payload: Mapping[str, object] | None = None,
        occurred_at: datetime | None = None,
    ) -> "TaskEvent":
        """创建一条合法、不可变的任务审计事件。"""

        if sequence <= 0:
            raise ValueError("sequence must be positive")

        normalized_stage: str | None = None
        if stage is not None:
            normalized_stage = stage.strip()
            if not normalized_stage:
                raise ValueError("stage must not be blank")

        timestamp = occurred_at or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")

        return cls(
            task_id=task_id,
            sequence=sequence,
            event_type=event_type,
            stage=normalized_stage,
            payload=dict(payload or {}),
            occurred_at=timestamp.astimezone(UTC),
        )