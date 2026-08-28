from uuid import uuid4

import pytest

from evidenceforge.testing import FakeTaskQueue


@pytest.mark.anyio
async def test_task_queue_records_an_enqueued_task_id() -> None:
    queue = FakeTaskQueue()
    task_id = uuid4()

    await queue.enqueue(task_id)

    assert queue.enqueued_task_ids == [task_id]
