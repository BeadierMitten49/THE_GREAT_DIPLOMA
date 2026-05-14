import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/references/products"

_VALID = {
    "name": "Сахар фасованный",
    "units_per_box": 12,
    "shelf_life_days": 365,
    "critical_stock": 100,
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


async def test_create_invalid_units_per_box_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={**_VALID, "units_per_box": 0})
    assert r.status_code == 422


async def test_get_by_id_returns_200_with_empty_recipe(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved
    assert data["recipe"] == []


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_update_returns_200_with_new_data(client: AsyncClient, saved: int) -> None:
    r = await client.patch(
        f"{BASE}/{saved}",
        json={**_VALID, "name": "Соль фасованная", "units_per_box": 24},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Соль фасованная"
    assert data["units_per_box"] == 24


async def test_set_recipe_returns_204(client: AsyncClient, saved: int) -> None:
    body = {
        "lines": [
            {"raw_material_id": 1, "consumption_per_unit": "1.5", "waste_percentage": "2.0"},
            {"raw_material_id": 2, "consumption_per_unit": "0.5", "waste_percentage": "0"},
        ]
    }
    r = await client.put(f"{BASE}/{saved}/recipe", json=body)
    assert r.status_code == 204


async def test_set_recipe_invalid_consumption_returns_422(client: AsyncClient, saved: int) -> None:
    body = {"lines": [{"raw_material_id": 1, "consumption_per_unit": "0", "waste_percentage": "0"}]}
    r = await client.put(f"{BASE}/{saved}/recipe", json=body)
    assert r.status_code == 422


async def test_set_recipe_not_found_returns_404(client: AsyncClient) -> None:
    body = {"lines": [{"raw_material_id": 1, "consumption_per_unit": "1", "waste_percentage": "0"}]}
    r = await client.put(f"{BASE}/999/recipe", json=body)
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
