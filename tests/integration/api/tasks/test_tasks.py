import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/tasks"


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------


async def test_get_tasks_empty(client: AsyncClient) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert r.json() == []


async def test_get_tasks_returns_list(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_get_tasks_filter_by_status(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.get(BASE, params={"status": "created"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"status": "in_progress"})
    assert r.status_code == 200
    assert len(r.json()) == 0


async def test_get_tasks_production_user_sees_own_only(
    production_client: AsyncClient,
    task_svc,
) -> None:
    from datetime import date
    from src.domain.tasks.entities import ProductionTask
    from src.domain.tasks.value_objects import TaskType
    defaults = dict(product_id=1, quantity=100, start_date=date(2026, 6, 1),
                    deadline=date(2026, 6, 10), task_type=TaskType.stock_task)
    task_svc._tasks[1] = ProductionTask(id=1, executor_id=2, **defaults)
    task_svc._tasks[2] = ProductionTask(id=2, executor_id=99, **defaults)
    # Production user (id=2) should see only their task
    r = await production_client.get(BASE)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["executor_id"] == 2


# ---------------------------------------------------------------------------
# GET /tasks/{id}
# ---------------------------------------------------------------------------


async def test_get_task_returns_200(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.get(f"{BASE}/{saved_task_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved_task_id
    assert data["status"] == "created"
    assert data["task_type"] == "stock_task"


async def test_get_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------


async def test_create_task_returns_201(client: AsyncClient) -> None:
    r = await client.post(BASE, json={
        "product_id": 1,
        "quantity": 200,
        "executor_id": 2,
        "start_date": "2026-06-01",
        "deadline": "2026-06-15",
        "task_type": "stock_task",
    })
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert "insufficient_materials" in data


async def test_create_task_with_order_id(client: AsyncClient) -> None:
    r = await client.post(BASE, json={
        "product_id": 1, "quantity": 100, "executor_id": 2,
        "start_date": "2026-06-01", "deadline": "2026-06-10",
        "task_type": "order_task", "order_id": 5,
    })
    assert r.status_code == 201


async def test_create_task_missing_field_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={"product_id": 1})
    assert r.status_code == 422


async def test_create_task_forbidden_for_production(production_client: AsyncClient) -> None:
    r = await production_client.post(BASE, json={
        "product_id": 1, "quantity": 100, "executor_id": 2,
        "start_date": "2026-06-01", "deadline": "2026-06-10", "task_type": "stock_task",
    })
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# POST /tasks/{id}/start
# ---------------------------------------------------------------------------


async def test_start_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.post(f"{BASE}/{saved_task_id}/start")
    assert r.status_code == 204


async def test_start_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/start")
    assert r.status_code == 404


async def test_start_task_invalid_transition_returns_422(
    client: AsyncClient, saved_task_id: int
) -> None:
    await client.post(f"{BASE}/{saved_task_id}/start")
    r = await client.post(f"{BASE}/{saved_task_id}/start")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /tasks/{id}/stop
# ---------------------------------------------------------------------------


async def test_stop_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    await client.post(f"{BASE}/{saved_task_id}/start")
    r = await client.post(f"{BASE}/{saved_task_id}/stop", json={"reason": "machine broke"})
    assert r.status_code == 204


async def test_stop_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/stop", json={"reason": "r"})
    assert r.status_code == 404


async def test_stop_task_missing_reason_returns_422(
    client: AsyncClient, saved_task_id: int
) -> None:
    r = await client.post(f"{BASE}/{saved_task_id}/stop", json={})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /tasks/{id}/resume
# ---------------------------------------------------------------------------


async def test_resume_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    await client.post(f"{BASE}/{saved_task_id}/start")
    await client.post(f"{BASE}/{saved_task_id}/stop", json={"reason": "r"})
    r = await client.post(f"{BASE}/{saved_task_id}/resume")
    assert r.status_code == 204


async def test_resume_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/resume")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks/{id}/complete
# ---------------------------------------------------------------------------


async def test_complete_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    await client.post(f"{BASE}/{saved_task_id}/start")
    r = await client.post(f"{BASE}/{saved_task_id}/complete", json={
        "actual_quantity": 95,
        "consumptions": [{"raw_material_id": 1, "actual_qty": "48.5"}],
    })
    assert r.status_code == 204


async def test_complete_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/complete", json={"actual_quantity": 90, "consumptions": []})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks/{id}/close
# ---------------------------------------------------------------------------


async def test_close_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    await client.post(f"{BASE}/{saved_task_id}/start")
    await client.post(f"{BASE}/{saved_task_id}/complete", json={
        "actual_quantity": 90, "consumptions": [],
    })
    r = await client.post(f"{BASE}/{saved_task_id}/close")
    assert r.status_code == 204


async def test_close_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/close")
    assert r.status_code == 404


async def test_close_task_forbidden_for_production(
    production_client: AsyncClient, task_svc
) -> None:
    # Manually insert a completed task
    from src.domain.tasks.entities import ProductionTask
    from src.domain.tasks.value_objects import TaskStatus, TaskType
    from datetime import date
    t = ProductionTask(
        id=99, product_id=1, quantity=100, executor_id=2,
        start_date=date(2026, 6, 1), deadline=date(2026, 6, 10),
        task_type=TaskType.stock_task, status=TaskStatus.completed,
    )
    task_svc._tasks[99] = t
    r = await production_client.post(f"{BASE}/99/close")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /tasks/{id}/assignee
# ---------------------------------------------------------------------------


async def test_reassign_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.patch(f"{BASE}/{saved_task_id}/assignee", json={"executor_id": 5})
    assert r.status_code == 204


async def test_reassign_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(f"{BASE}/999/assignee", json={"executor_id": 5})
    assert r.status_code == 404


async def test_reassign_task_forbidden_for_production(
    production_client: AsyncClient, task_svc
) -> None:
    from datetime import date
    from src.domain.tasks.entities import ProductionTask
    from src.domain.tasks.value_objects import TaskType
    task_svc._tasks[1] = ProductionTask(
        id=1, product_id=1, quantity=100, executor_id=2,
        start_date=date(2026, 6, 1), deadline=date(2026, 6, 10), task_type=TaskType.stock_task,
    )
    r = await production_client.patch(f"{BASE}/1/assignee", json={"executor_id": 5})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /tasks/{id}
# ---------------------------------------------------------------------------


async def test_delete_task_returns_204(client: AsyncClient, saved_task_id: int) -> None:
    r = await client.delete(f"{BASE}/{saved_task_id}")
    assert r.status_code == 204


async def test_delete_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.delete(f"{BASE}/999")
    assert r.status_code == 404


async def test_delete_task_forbidden_for_production(
    production_client: AsyncClient, task_svc
) -> None:
    from datetime import date
    from src.domain.tasks.entities import ProductionTask
    from src.domain.tasks.value_objects import TaskType
    task_svc._tasks[1] = ProductionTask(
        id=1, product_id=1, quantity=100, executor_id=2,
        start_date=date(2026, 6, 1), deadline=date(2026, 6, 10), task_type=TaskType.stock_task,
    )
    r = await production_client.delete(f"{BASE}/1")
    assert r.status_code == 403
