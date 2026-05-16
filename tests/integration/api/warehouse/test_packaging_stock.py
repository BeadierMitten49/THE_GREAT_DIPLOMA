import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/warehouse/packaging-stock"

ARRIVAL_BODY = {"packaging_id": 1, "quantity": 500, "comment": None}


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
    r = await client.post(BASE, json={"quantity": 100})
    assert r.status_code == 422


async def test_get_by_id_returns_200(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved
    assert data["packaging_id"] == 1
    assert data["quantity"] == 500


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_get_list_filtered_by_packaging_id(client: AsyncClient, saved: int) -> None:
    r = await client.get(BASE, params={"packaging_id": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"packaging_id": 999})
    assert r.status_code == 200
    assert r.json() == []


async def test_write_off_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": 100})
    assert r.status_code == 204


async def test_write_off_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/write-off", json={"amount": 10})
    assert r.status_code == 404


async def test_write_off_exceeds_quantity_returns_422(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": 9999})
    assert r.status_code == 422
