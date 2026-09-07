from collections.abc import Iterator
from uuid import UUID, uuid4

import anyio
import pytest
from fastapi.testclient import TestClient

from evidenceforge.api.deps import (
    get_source_snapshot_service,
    get_task_event_service,
    get_task_event_stream_service,
    get_task_service,
)
from evidenceforge.api.routers.research_tasks import (
    stream_research_task_events,
)
from evidenceforge.api.schemas import TaskEventResponse
from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.application.task_event_stream_service import (
    TaskEventStreamService,
)
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
    task_event_stream_service = TaskEventStreamService(
        task_event_service=task_event_service,
        poll_interval_seconds=0.01,
    )

    app.dependency_overrides[get_task_event_stream_service] = lambda: (
        task_event_stream_service
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

@pytest.mark.anyio
async def test_stream_research_task_events_returns_sse_replay() -> None:
    task_repository = FakeTaskRepository()
    event_repository = FakeTaskEventRepository()
    task_event_service = TaskEventService(
        task_repository=task_repository,
        event_repository=event_repository,
    )
    stream_service = TaskEventStreamService(
        task_event_service=task_event_service,
        poll_interval_seconds=0.01,
    )
    task = ResearchTask.create(
        question="验证 SSE 事件回放协议",
    )

    await task_repository.add(task)
    created_event = await event_repository.append(
        task_id=task.id,
        event_type=TaskEventType.CREATED,
        payload={"status": "queued"},
    )

    response = await stream_research_task_events(
        task.id,
        task_event_service=task_event_service,
        stream_service=stream_service,
    )

    assert response.media_type == "text/event-stream"

    first_chunk = await anext(response.body_iterator)

    expected_event = TaskEventResponse(
        sequence=created_event.sequence,
        event_type=created_event.event_type,
        stage=created_event.stage,
        payload=dict(created_event.payload),
        occurred_at=created_event.occurred_at,
    )

    assert first_chunk == (
        f"id: {created_event.sequence}\n"
        "event: task_event\n"
        f"data: {expected_event.model_dump_json()}\n\n"
    )

    await response.body_iterator.aclose()


def test_stream_research_task_events_returns_404_for_an_unknown_task(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/research-tasks/{uuid4()}/events/stream",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "research task not found",
    }