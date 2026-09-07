from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import TaskStatus


class ResearchTaskCreateRequest(BaseModel):
    """创建调研任务的 HTTP 请求模型。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    question: str = Field(min_length=1)


class ResearchTaskResponse(BaseModel):
    """返回给 API 调用方的任务模型。"""

    task_id: UUID
    question: str
    status: TaskStatus


class SourceSnapshotResponse(BaseModel):
    """返回给 API 调用方的不可变来源快照。"""

    snapshot_id: UUID
    source_uri: str
    source_kind: str
    raw_content: str
    content_hash: str
    captured_at: datetime

class TaskEventResponse(BaseModel):
    """返回给 API 调用方的任务生命周期事件。"""

    sequence: int
    event_type: TaskEventType
    stage: str | None
    payload: dict[str, object]
    occurred_at: datetime