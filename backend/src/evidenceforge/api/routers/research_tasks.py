from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from evidenceforge.api.deps import get_task_service
from evidenceforge.api.schemas import (
    ResearchTaskCreateRequest,
    ResearchTaskResponse,
)
from evidenceforge.application.task_service import TaskService

TaskServiceDependency = Annotated[
    TaskService,
    Depends(get_task_service),
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
