from fastapi import APIRouter, Depends, status

from src.application.tasks.dto import CompleteTaskDTO, ConsumptionInputDTO
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.domain.tasks.value_objects import TaskStatus
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.dependencies import director_only, director_or_production
from src.presentation.api.v1.tasks.dependencies import get_task_service
from src.presentation.api.v1.tasks.schemas import (
    CompleteTaskRequest,
    CreateTaskRequest,
    CreateTaskResponse,
    ReassignTaskRequest,
    StopTaskRequest,
    TaskResponse,
)
from src.presentation.api.v1.tasks.service import ProductionTaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _task_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        product_id=task.product_id,
        quantity=task.quantity,
        executor_id=task.executor_id,
        start_date=task.start_date,
        deadline=task.deadline,
        task_type=task.task_type,
        status=task.status,
        order_id=task.order_id,
        comment=task.comment,
        created_at=task.created_at,
        actual_start_at=task.actual_start_at,
        actual_end_at=task.actual_end_at,
    )


@router.get("", response_model=list[TaskResponse], dependencies=[director_or_production])
async def get_tasks(
    status: TaskStatus | None = None,
    executor_id: int | None = None,
    current_user: User = Depends(get_current_user),
    service: ProductionTaskService = Depends(get_task_service),
):
    if current_user.has_role(Role.production) and not current_user.has_role(Role.director):
        executor_id = current_user.id
    tasks = await service.get_all(status=status, executor_id=executor_id)
    return [_task_response(t) for t in tasks]


@router.get("/{id}", response_model=TaskResponse, dependencies=[director_or_production])
async def get_task(
    id: int,
    current_user: User = Depends(get_current_user),
    service: ProductionTaskService = Depends(get_task_service),
):
    task = await service.get(id)
    return _task_response(task)


@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[director_only])
async def create_task(
    body: CreateTaskRequest,
    service: ProductionTaskService = Depends(get_task_service),
):
    task_id, insufficient = await service.create(
        product_id=body.product_id,
        quantity=body.quantity,
        executor_id=body.executor_id,
        start_date=body.start_date,
        deadline=body.deadline,
        task_type=body.task_type,
        order_id=body.order_id,
        comment=body.comment,
    )
    return CreateTaskResponse(id=task_id, insufficient_materials=insufficient)


@router.post("/{id}/start", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_production])
async def start_task(id: int, service: ProductionTaskService = Depends(get_task_service)):
    await service.start(id)


@router.post("/{id}/stop", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_production])
async def stop_task(
    id: int,
    body: StopTaskRequest,
    service: ProductionTaskService = Depends(get_task_service),
):
    await service.stop(id, body.reason)


@router.post("/{id}/resume", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_production])
async def resume_task(id: int, service: ProductionTaskService = Depends(get_task_service)):
    await service.resume(id)


@router.post("/{id}/complete", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_or_production])
async def complete_task(
    id: int,
    body: CompleteTaskRequest,
    service: ProductionTaskService = Depends(get_task_service),
):
    dto = CompleteTaskDTO(
        task_id=id,
        actual_quantity=body.actual_quantity,
        comment=body.comment,
        consumptions=[
            ConsumptionInputDTO(
                raw_material_id=c.raw_material_id,
                actual_qty=c.actual_qty,
                waste_qty=c.waste_qty,
            )
            for c in body.consumptions
        ],
    )
    await service.complete(dto)


@router.post("/{id}/close", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[director_only])
async def close_task(id: int, service: ProductionTaskService = Depends(get_task_service)):
    await service.close(id)


@router.patch("/{id}/assignee", status_code=status.HTTP_204_NO_CONTENT,
              dependencies=[director_only])
async def reassign_task(
    id: int,
    body: ReassignTaskRequest,
    service: ProductionTaskService = Depends(get_task_service),
):
    await service.reassign(id, body.executor_id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[director_only])
async def delete_task(id: int, service: ProductionTaskService = Depends(get_task_service)):
    await service.delete(id)
