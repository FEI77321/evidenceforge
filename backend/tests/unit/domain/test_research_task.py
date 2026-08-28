import pytest

from evidenceforge.domain.tasks import (
    InvalidTaskTransition,
    ResearchTask,
    TaskStatus,
)


def make_task() -> ResearchTask:
    return ResearchTask.create(
        question="FastAPI 的 BackgroundTasks 何时适合，何时应使用独立任务队列？"
    )


def test_new_task_starts_queued() -> None:
    task = make_task()

    assert task.status is TaskStatus.QUEUED


def test_task_can_follow_the_success_path() -> None:
    task = make_task()

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)

    assert task.status is TaskStatus.COMPLETED
    assert task.is_terminal is True


@pytest.mark.parametrize(
    "initial_status",
    [
        TaskStatus.QUEUED,
        TaskStatus.RUNNING,
    ],
)
def test_active_task_can_request_cancellation(
    initial_status: TaskStatus,
) -> None:
    task = make_task()

    if initial_status is TaskStatus.RUNNING:
        task.transition_to(TaskStatus.RUNNING)

    accepted = task.request_cancellation()

    assert accepted is True
    assert task.status is TaskStatus.CANCEL_REQUESTED
    assert task.is_terminal is False


def test_cancel_request_is_idempotent() -> None:
    task = make_task()

    assert task.request_cancellation() is True
    assert task.request_cancellation() is False
    assert task.status is TaskStatus.CANCEL_REQUESTED


def test_only_a_cancel_requested_task_can_be_marked_canceled() -> None:
    task = make_task()

    with pytest.raises(InvalidTaskTransition):
        task.transition_to(TaskStatus.CANCELED)

    task.request_cancellation()
    task.transition_to(TaskStatus.CANCELED)

    assert task.status is TaskStatus.CANCELED
    assert task.is_terminal is True


def test_task_can_fail_only_after_it_has_started() -> None:
    task = make_task()

    with pytest.raises(InvalidTaskTransition):
        task.transition_to(TaskStatus.FAILED)

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.FAILED)

    assert task.status is TaskStatus.FAILED
    assert task.is_terminal is True


@pytest.mark.parametrize(
    "terminal_status",
    [
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELED,
    ],
)
def test_terminal_task_ignores_later_cancellation_requests(
    terminal_status: TaskStatus,
) -> None:
    task = make_task()

    if terminal_status is TaskStatus.COMPLETED:
        task.transition_to(TaskStatus.RUNNING)
        task.transition_to(TaskStatus.COMPLETED)
    elif terminal_status is TaskStatus.FAILED:
        task.transition_to(TaskStatus.RUNNING)
        task.transition_to(TaskStatus.FAILED)
    else:
        task.request_cancellation()
        task.transition_to(TaskStatus.CANCELED)

    accepted = task.request_cancellation()

    assert accepted is False
    assert task.status is terminal_status
    assert task.is_terminal is True


def test_task_question_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="question must not be blank"):
        ResearchTask.create(question="   ")
