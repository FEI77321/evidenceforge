from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from evidenceforge.main import app

client = TestClient(app)


def test_create_research_task_returns_202_and_queued_task() -> None:
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


def test_create_research_task_rejects_a_blank_question() -> None:
    response = client.post(
        "/api/v1/research-tasks",
        json={
            "question": "   ",
        },
    )

    assert response.status_code == 422


def test_get_research_task_returns_an_existing_task() -> None:
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


def test_get_research_task_returns_404_for_unknown_id() -> None:
    response = client.get(f"/api/v1/research-tasks/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "research task not found",
    }


def test_cancel_research_task_requests_cancellation_idempotently() -> None:
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
