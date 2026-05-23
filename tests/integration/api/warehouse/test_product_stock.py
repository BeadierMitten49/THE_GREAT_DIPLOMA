import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/warehouse/product-stock"

ARRIVAL_BODY = {
    "product_id": 1,
    "quantity": 100,
    "arrival_date": "2026-05-01",
    "expiry_date": "2026-11-01",
    "comment": None,
}


@pytest.fixture
async def saved(client: AsyncClient) -> int:
    r = await client.post(BASE, json=ARRIVAL_BODY)
    return r.json()["id"]


async def test_get_list_empty(client: AsyncClient) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert r.json() == []


async def test_arrival_returns_201_with_id(client: AsyncClient) -> None:
    r = await client.post(BASE, json=ARRIVAL_BODY)
    assert r.status_code == 201
    assert r.json()["id"] == 1


async def test_arrival_missing_field_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={"product_id": 1, "quantity": 50})
    assert r.status_code == 422


async def test_get_by_id_returns_200(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved
    assert data["product_id"] == 1
    assert data["quantity"] == 100
    assert data["batch_number"] == 1


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_get_list_filtered_by_product_id(client: AsyncClient, saved: int) -> None:
    r = await client.get(BASE, params={"product_id": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"product_id": 999})
    assert r.status_code == 200
    assert r.json() == []


async def test_write_off_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": 10})
    assert r.status_code == 204


async def test_write_off_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/write-off", json={"amount": 10})
    assert r.status_code == 404


async def test_write_off_exceeds_quantity_returns_422(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": 9999})
    assert r.status_code == 422


async def test_adjust_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.patch(f"{BASE}/{saved}", json={"quantity": 42, "comment": "fixed"})
    assert r.status_code == 204


async def test_adjust_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(f"{BASE}/999", json={"quantity": 1})
    assert r.status_code == 404


async def test_adjust_negative_quantity_returns_422(client: AsyncClient, saved: int) -> None:
    r = await client.patch(f"{BASE}/{saved}", json={"quantity": -1})
    assert r.status_code == 422


async def test_pending_tasks_returns_list(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/pending-tasks")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["actual_quantity"] == 95
    assert data[0]["planned_quantity"] == 100


async def test_accept_from_task_returns_201(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/from-task", json={"task_id": 1})
    assert r.status_code == 201
    assert "id" in r.json()


async def test_accept_from_task_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/from-task", json={"task_id": 999})
    assert r.status_code == 404


async def test_response_contains_reserved_field(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert "reserved" in data
    assert data["reserved"] == 0
    assert "reserved_orders" in data
    assert data["reserved_orders"] == []
