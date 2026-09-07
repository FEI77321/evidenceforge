from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.application.task_service import TaskService
from evidenceforge.infrastructure.celery_task_queue import CeleryTaskQueue
from evidenceforge.infrastructure.database import async_session_factory
from evidenceforge.infrastructure.persistence.source_snapshot_repository import (
    PostgreSQLSourceSnapshotRepository,
)
from evidenceforge.infrastructure.persistence.task_event_repository import (
    PostgreSQLTaskEventRepository,
)
from evidenceforge.infrastructure.persistence.task_repository import (
    PostgreSQLTaskRepository,
)

_queue = CeleryTaskQueue()


def get_task_service() -> TaskService:
    """为 API Router 提供真实持久化的任务应用服务。"""

    repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )
    event_repository = PostgreSQLTaskEventRepository(
        session_factory=async_session_factory,
    )

    return TaskService(
        repository=repository,
        event_repository=event_repository,
        queue=_queue,
    )


def get_source_snapshot_service() -> SourceSnapshotService:
    """为 API Router 提供真实持久化的来源快照读取服务。"""

    task_repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )
    snapshot_repository = PostgreSQLSourceSnapshotRepository(
        session_factory=async_session_factory,
    )

    return SourceSnapshotService(
        task_repository=task_repository,
        snapshot_repository=snapshot_repository,
    )


def get_task_event_service() -> TaskEventService:
    """为 API Router 提供真实持久化的任务事件读取服务。"""

    task_repository = PostgreSQLTaskRepository(
        session_factory=async_session_factory,
    )
    event_repository = PostgreSQLTaskEventRepository(
        session_factory=async_session_factory,
    )

    return TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )