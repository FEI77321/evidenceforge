from datetime import UTC, datetime
from uuid import UUID

import pytest

from evidenceforge.domain.sources import SourceSnapshot


def test_create_normalizes_source_identity_and_calculates_hash() -> None:
    task_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    captured_at = datetime(2026, 9, 4, tzinfo=UTC)

    snapshot = SourceSnapshot.create(
        task_id=task_id,
        source_uri=" fixture://fastapi_background_tasks.md ",
        source_kind=" fixture ",
        raw_content="FastAPI BackgroundTasks",
        snapshot_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        captured_at=captured_at,
    )

    assert snapshot.id == UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert snapshot.task_id == task_id
    assert snapshot.source_uri == "fixture://fastapi_background_tasks.md"
    assert snapshot.source_kind == "fixture"
    assert snapshot.raw_content == "FastAPI BackgroundTasks"
    assert (
        snapshot.content_hash
        == "f0bfcf115bedb271798f03f063cef15bbf1f8011f878bf311480e42c36ee4ca2"
    )
    assert snapshot.captured_at == captured_at


@pytest.mark.parametrize(
    ("source_uri", "source_kind", "error_message"),
    [
        ("   ", "fixture", "source_uri must not be blank"),
        ("fixture://example.md", "   ", "source_kind must not be blank"),
    ],
)
def test_create_rejects_blank_source_identity(
    source_uri: str,
    source_kind: str,
    error_message: str,
) -> None:
    with pytest.raises(ValueError, match=error_message):
        SourceSnapshot.create(
            task_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            source_uri=source_uri,
            source_kind=source_kind,
            raw_content="content",
        )
