from collections.abc import Iterator
from uuid import UUID, uuid4

import anyio
import pytest
from fastapi.testclient import TestClient

from evidenceforge.api.deps import (
    get_source_snapshot_service,
    get_task_event_service,
    get_task_service,
)
from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.application.task_service import TaskService
from evidenceforge.domain.events import TaskEventType
from evidenceforge.domain.tasks import ResearchTask
from evidenceforge.main import app
from evidenceforge.testing import (
    FakeSourceSnapshotRepository,
    FakeTaskEventRepository,
    FakeTaskQueue,
    FakeTaskRepository,
)


@pytest.fixture
def snapshot_repository() -> FakeSourceSnapshotRepository:
    return FakeSourceSnapshotRepository()


@pytest.fixture
def client(
    task_repository: FakeTaskRepository,
    snapshot_repository: FakeSourceSnapshotRepository,
    event_repository: FakeTaskEventRepository,
) -> Iterator[TestClient]:
    queue = FakeTaskQueue()
    task_service = TaskService(
        repository=task_repository,
        event_repository=event_repository,
        queue=queue,
    )
    source_snapshot_service = SourceSnapshotService(
        task_repository=task_repository,
        snapshot_repository=snapshot_repository,
    )
    task_event_service = TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )

    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_source_snapshot_service] = lambda: (
        source_snapshot_service
    )
    app.dependency_overrides[get_task_event_service] = lambda: (
        task_event_service
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def task_repository() -> FakeTaskRepository:
    return FakeTaskRepository()


@pytest.fixture
def event_repository() -> FakeTaskEventRepository:
    return FakeTaskEventRepository()

def test_list_research_task_events_returns_ordered_events(
    client: TestClient,
    event_repository: FakeTaskEventRepository,
) -> None:
    create_response = client.post(
        "/api/v1/research-tasks",
        json={"question": "调研任务事件时间线的读取语义"},
    )
    task_id = UUID(create_response.json()["task_id"])

    async def append_running_event() -> None:
        await event_repository.append(
            task_id=task_id,
            event_type=TaskEventType.RUNNING,
            payload={"status": "running"},
        )

    anyio.run(append_running_event)

    response = client.get(f"/api/v1/research-tasks/{task_id}/events")

    assert response.status_code == 200

    payload = response.json()

    assert [
        (
            event["sequence"],
            event["event_type"],
            event["stage"],
            event["payload"],
        )
        for event in payload
    ] == [
        (1, "created", None, {"status": "queued"}),
        (2, "running", None, {"status": "running"}),
    ]
    assert all(
        event["occurred_at"].endswith("Z")
        for event in payload
    )


def test_list_research_task_events_returns_an_empty_list_for_existing_task(
    client: TestClient,
    task_repository: FakeTaskRepository,
) -> None:
    task = ResearchTask.create(
        question="存在但尚未写入事件的历史任务",
    )
    anyio.run(task_repository.add, task)

    response = client.get(f"/api/v1/research-tasks/{task.id}/events")

    assert response.status_code == 200
    assert response.json() == []


def test_list_research_task_events_returns_404_for_an_unknown_task(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/research-tasks/{uuid4()}/events",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "research task not found",
    }