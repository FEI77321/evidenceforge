import asyncio
from collections.abc import AsyncIterator, Sequence
from uuid import UUID

from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.domain.events import TaskEvent


class TaskEventStreamService:
    """回放并持续读取指定任务的新增生命周期事件。"""

    def __init__(
        self,
        *,
        task_event_service: TaskEventService,
        poll_interval_seconds: float = 0.2,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")

        self._task_event_service = task_event_service
        self._poll_interval_seconds = poll_interval_seconds

    async def stream_events(
        self,
        task_id: UUID,
        *,
        initial_events: Sequence[TaskEvent],
    ) -> AsyncIterator[TaskEvent]:
        """先回放已有事件，再按 sequence 推送后续新增事件。"""

        last_sent_sequence = 0

        for event in initial_events:
            if event.sequence <= last_sent_sequence:
                continue

            last_sent_sequence = event.sequence
            yield event

        while True:
            events = await self._task_event_service.list_events(task_id)
            if events is None:
                return

            for event in events:
                if event.sequence <= last_sent_sequence:
                    continue

                last_sent_sequence = event.sequence
                yield event

            await asyncio.sleep(self._poll_interval_seconds)