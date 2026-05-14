import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/references/raw-materials"

_VALID = {
    "name": "Сахар-сырец",
    "unit": "кг",
    "shelf_life_days": 730,
    "critical_stock": "50.00",
}


@pytest.fixture
async def saved(client: AsyncClient) -> int:
    r = await client.post(BASE, json=_VALID)
    return r.json()["id"]


async def test_create_returns_201_with_id(client: AsyncClient) -> None:
    r = await client.post(BASE, json=_VALID)
    assert r.status_code == 201
    assert r.json()["id"] == 1


async def test_create_duplicate_returns_409(client: AsyncClient, saved: int) -> None:
    r = await client.post(BASE, json=_VALID)
    assert r.status_code == 409


async def test_create_invalid_shelf_life_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={**_VALID, "shelf_life_days": 0})
    assert r.status_code == 422


async def test_create_negative_critical_stock_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={**_VALID, "critical_stock": "-1"})
    assert r.status_code == 422


async def test_get_by_id_returns_200(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Сахар-сырец"
    assert data["unit"] == "кг"
    assert data["is_active"] is True


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_update_returns_200_with_new_data(client: AsyncClient, saved: int) -> None:
    r = await client.patch(
        f"{BASE}/{saved}", json={**_VALID, "name": "Соль", "shelf_life_days": 1000}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Соль"
    assert data["shelf_life_days"] == 1000


async def test_update_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(f"{BASE}/999", json=_VALID)
    assert r.status_code == 404


async def test_deactivate_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/deactivate")
    assert r.status_code == 204


async def test_activate_returns_204(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.post(f"{BASE}/{saved}/activate")
    assert r.status_code == 204


async def test_get_list_excludes_inactive_by_default(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.get(BASE)
    assert r.json() == []


async def test_get_list_include_inactive(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.get(BASE, params={"include_inactive": True})
    assert len(r.json()) == 1
