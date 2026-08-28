from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class TaskStatus(StrEnum):
    """一次调研任务的生命周期状态。"""

    QUEUED = "queued"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class InvalidTaskTransition(ValueError):
    """任务状态迁移不符合生命周期规则时抛出。"""


_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.QUEUED: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.CANCEL_REQUESTED,
        }
    ),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCEL_REQUESTED,
        }
    ),
    TaskStatus.CANCEL_REQUESTED: frozenset(
        {
            TaskStatus.CANCELED,
        }
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELED: frozenset(),
}

_TERMINAL_STATUSES = frozenset(
    {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELED,
    }
)


@dataclass
class ResearchTask:
    """一次调研任务的核心领域实体。"""

    id: UUID
    question: str
    _status: TaskStatus = field(
        default=TaskStatus.QUEUED,
        init=False,
        repr=False,
    )

    @classmethod
    def create(
        cls,
        question: str,
        *,
        task_id: UUID | None = None,
    ) -> "ResearchTask":
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be blank")

        return cls(
            id=task_id or uuid4(),
            question=normalized_question,
        )

    @property
    def status(self) -> TaskStatus:
        """返回任务当前状态。"""

        return self._status

    @property
    def is_terminal(self) -> bool:
        """判断任务是否已经进入终态。"""

        return self._status in _TERMINAL_STATUSES

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        """判断任务是否允许迁移到目标状态。"""

        return next_status in _ALLOWED_TRANSITIONS[self._status]

    def transition_to(self, next_status: TaskStatus) -> None:
        """将任务迁移到目标状态，非法迁移会被拒绝。"""

        if not self.can_transition_to(next_status):
            raise InvalidTaskTransition(
                f"cannot transition task from {self._status.value} "
                f"to {next_status.value}"
            )

        self._status = next_status

    def request_cancellation(self) -> bool:
        """请求取消任务；只有首次接受请求时返回 True。"""

        if self.is_terminal or self._status is TaskStatus.CANCEL_REQUESTED:
            return False

        self.transition_to(TaskStatus.CANCEL_REQUESTED)
        return True
