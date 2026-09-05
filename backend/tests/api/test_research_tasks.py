from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import anyio
import pytest
from fastapi.testclient import TestClient

from evidenceforge.api.deps import (
    get_source_snapshot_service,
    get_task_service,
)
from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.application.task_service import TaskService
from evidenceforge.domain.sources import SourceSnapshot
from evidenceforge.main import app
from evidenceforge.testing import (
    FakeSourceSnapshotRepository,
    FakeTaskQueue,
    FakeTaskRepository,
)


@pytest.fixture
def snapshot_repository() -> FakeSourceSnapshotRepository:
    return FakeSourceSnapshotRepository()


@pytest.fixture
def client(
    snapshot_repository: FakeSourceSnapshotRepository,
) -> Iterator[TestClient]:
    task_repository = FakeTaskRepository()
    queue = FakeTaskQueue()
    task_service = TaskService(
        repository=task_repository,
        queue=queue,
    )
    source_snapshot_service = SourceSnapshotService(
        task_repository=task_repository,
        snapshot_repository=snapshot_repository,
    )

    app.dependency_overrides[get_task_service] = lambda: task_service
    app.dependency_overrides[get_source_snapshot_service] = lambda: (
        source_snapshot_service
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_create_research_task_returns_202_and_queued_task(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/research-tasks",
        json={
            "question": "  FastAPI 何时应该使用独立任务队列？  ",
        },
    )

    assert response.status_code == 202

    payload = response.json()

    assert set(payload) == {"task_id", "question", "status"}
    assert UUID(payload["task_id"])
    assert payload["question"] == "FastAPI 何时应该使用独立任务队列？"
    assert payload["status"] == "queued"


def test_create_research_task_rejects_a_blank_question(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/research-tasks",
        json={
            "question": "   ",
        },
    )

    assert response.status_code == 422


def test_get_research_task_returns_an_existing_task(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/research-tasks",
        json={
            "question": "调研 FastAPI 的依赖注入机制",
        },
    )
    task_id = create_response.json()["task_id"]

    response = client.get(f"/api/v1/research-tasks/{task_id}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["task_id"] == task_id
    assert payload["question"] == "调研 FastAPI 的依赖注入机制"
    assert payload["status"] == "queued"


def test_get_research_task_returns_404_for_unknown_id(
    client: TestClient,
) -> None:
    response = client.get(f"/api/v1/research-tasks/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "research task not found",
    }


def test_cancel_research_task_requests_cancellation_idempotently(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/research-tasks",
        json={
            "question": "调研 Celery 的任务取消语义",
        },
    )
    task_id = create_response.json()["task_id"]

    first_cancel_response = client.post(f"/api/v1/research-tasks/{task_id}/cancel")

    assert first_cancel_response.status_code == 200

    first_payload = first_cancel_response.json()

    assert first_payload["task_id"] == task_id
    assert first_payload["status"] == "cancel_requested"

    second_cancel_response = client.post(f"/api/v1/research-tasks/{task_id}/cancel")

    assert second_cancel_response.status_code == 200
    assert second_cancel_response.json()["status"] == "cancel_requested"


def test_list_research_task_sources_returns_existing_snapshots(
    client: TestClient,
    snapshot_repository: FakeSourceSnapshotRepository,
) -> None:
    create_response = client.post(
        "/api/v1/research-tasks",
        json={"question": "调研 FastAPI BackgroundTasks 的适用边界"},
    )
    task_id = UUID(create_response.json()["task_id"])
    snapshot = SourceSnapshot.create(
        task_id=task_id,
        source_uri="fixture://fastapi_background_tasks.md",
        source_kind="fixture",
        raw_content="FastAPI BackgroundTasks are useful for small tasks.",
        captured_at=datetime(2026, 9, 4, 6, 0, tzinfo=UTC),
    )
    anyio.run(snapshot_repository.add, snapshot)

    response = client.get(f"/api/v1/research-tasks/{task_id}/sources")

    assert response.status_code == 200
    assert response.json() == [
        {
            "snapshot_id": str(snapshot.id),
            "source_uri": "fixture://fastapi_background_tasks.md",
            "source_kind": "fixture",
            "raw_content": "FastAPI BackgroundTasks are useful for small tasks.",
            "content_hash": snapshot.content_hash,
            "captured_at": "2026-09-04T06:00:00Z",
        },
    ]


def test_list_research_task_sources_returns_an_empty_list_when_no_sources_exist(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/research-tasks",
        json={"question": "尚未被 Worker 执行的任务"},
    )
    task_id = create_response.json()["task_id"]

    response = client.get(f"/api/v1/research-tasks/{task_id}/sources")

    assert response.status_code == 200
    assert response.json() == []


def test_list_research_task_sources_returns_404_for_an_unknown_task(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/v1/research-tasks/{uuid4()}/sources",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "research task not found",
    }
