import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/warehouse/raw-material-stock"

ARRIVAL_BODY = {
    "raw_material_id": 1,
    "quantity": "50.0",
    "arrival_date": "2026-05-01",
    "expiry_date": "2026-12-31",
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
    r = await client.post(BASE, json={"raw_material_id": 1, "quantity": "10.0"})
    assert r.status_code == 422


async def test_get_by_id_returns_200(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved
    assert data["raw_material_id"] == 1


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_get_list_filtered_by_raw_material_id(client: AsyncClient, saved: int) -> None:
    r = await client.get(BASE, params={"raw_material_id": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"raw_material_id": 999})
    assert r.status_code == 200
    assert r.json() == []


async def test_write_off_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": "10.0"})
    assert r.status_code == 204


async def test_write_off_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/write-off", json={"amount": "10.0"})
    assert r.status_code == 404


async def test_write_off_exceeds_quantity_returns_422(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/write-off", json={"amount": "9999.0"})
    assert r.status_code == 422


async def test_response_includes_reserved_field(client: AsyncClient, saved: int) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert "reserved" in r.json()[0]

    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    assert "reserved" in r.json()


async def test_adjust_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.patch(f"{BASE}/{saved}", json={"quantity": "75.0", "comment": "corrected"})
    assert r.status_code == 204


async def test_adjust_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(f"{BASE}/999", json={"quantity": "75.0", "comment": None})
    assert r.status_code == 404


async def test_adjust_negative_quantity_returns_422(client: AsyncClient, saved: int) -> None:
    r = await client.patch(f"{BASE}/{saved}", json={"quantity": "-1.0", "comment": None})
    assert r.status_code == 422
