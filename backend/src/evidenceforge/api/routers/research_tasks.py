from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from evidenceforge.api.deps import (
    get_source_snapshot_service,
    get_task_event_service,
    get_task_service,
)
from evidenceforge.api.schemas import (
    ResearchTaskCreateRequest,
    ResearchTaskResponse,
    SourceSnapshotResponse,
    TaskEventResponse,
)
from evidenceforge.application.source_snapshot_service import (
    SourceSnapshotService,
)
from evidenceforge.application.task_event_service import TaskEventService
from evidenceforge.application.task_service import TaskService

TaskServiceDependency = Annotated[
    TaskService,
    Depends(get_task_service),
]

SourceSnapshotServiceDependency = Annotated[
    SourceSnapshotService,
    Depends(get_source_snapshot_service),
]

TaskEventServiceDependency = Annotated[
    TaskEventService,
    Depends(get_task_event_service),
]

router = APIRouter(
    prefix="/api/v1/research-tasks",
    tags=["research-tasks"],
)


@router.post(
    "",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_research_task(
    request: ResearchTaskCreateRequest,
    service: TaskServiceDependency,
) -> ResearchTaskResponse:
    """创建并投递一条调研任务。"""

    task = await service.create_task(question=request.question)

    return ResearchTaskResponse(
        task_id=task.id,
        question=task.question,
        status=task.status,
    )


@router.get(
    "/{task_id}",
    response_model=ResearchTaskResponse,
)
async def get_research_task(
    task_id: UUID,
    service: TaskServiceDependency,
) -> ResearchTaskResponse:
    """查询一条调研任务。"""

    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research task not found",
        )

    return ResearchTaskResponse(
        task_id=task.id,
        question=task.question,
        status=task.status,
    )


@router.post(
    "/{task_id}/cancel",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_research_task(
    task_id: UUID,
    service: TaskServiceDependency,
) -> ResearchTaskResponse:
    """请求取消一条调研任务。"""

    task = await service.cancel_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research task not found",
        )

    return ResearchTaskResponse(
        task_id=task.id,
        question=task.question,
        status=task.status,
    )


@router.get(
    "/{task_id}/sources",
    response_model=list[SourceSnapshotResponse],
)
async def list_research_task_sources(
    task_id: UUID,
    service: SourceSnapshotServiceDependency,
) -> list[SourceSnapshotResponse]:
    """读取一条调研任务保存的来源快照。"""

    snapshots = await service.list_sources(task_id)
    if snapshots is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research task not found",
        )

    return [
        SourceSnapshotResponse(
            snapshot_id=snapshot.id,
            source_uri=snapshot.source_uri,
            source_kind=snapshot.source_kind,
            raw_content=snapshot.raw_content,
            content_hash=snapshot.content_hash,
            captured_at=snapshot.captured_at,
        )
        for snapshot in snapshots
    ]

@router.get(
    "/{task_id}/events",
    response_model=list[TaskEventResponse],
)
async def list_research_task_events(
    task_id: UUID,
    service: TaskEventServiceDependency,
) -> list[TaskEventResponse]:
    """读取一条调研任务的生命周期事件。"""

    events = await service.list_events(task_id)
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="research task not found",
        )

    return [
        TaskEventResponse(
            sequence=event.sequence,
            event_type=event.event_type,
            stage=event.stage,
            payload=dict(event.payload),
            occurred_at=event.occurred_at,
        )
        for event in events
    ]