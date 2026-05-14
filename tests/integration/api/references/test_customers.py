import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/references/customers"


@pytest.fixture
async def saved(client: AsyncClient) -> int:
    r = await client.post(BASE, json={"name": "ООО Ромашка", "default_address": "ул. Ленина, 1"})
    return r.json()["id"]


async def test_get_list_empty(client: AsyncClient) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert r.json() == []


async def test_create_returns_201_with_id(client: AsyncClient) -> None:
    r = await client.post(BASE, json={"name": "ООО Ромашка", "default_address": "ул. Ленина, 1"})
    assert r.status_code == 201
    assert r.json()["id"] == 1


async def test_create_duplicate_returns_409(client: AsyncClient, saved: int) -> None:
    r = await client.post(BASE, json={"name": "ООО Ромашка", "default_address": "другой адрес"})
    assert r.status_code == 409


async def test_create_missing_field_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={"name": "ООО Ромашка"})
    assert r.status_code == 422


async def test_get_by_id_returns_200(client: AsyncClient, saved: int) -> None:
    r = await client.get(f"{BASE}/{saved}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved
    assert data["name"] == "ООО Ромашка"
    assert data["is_active"] is True


async def test_get_by_id_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


async def test_get_list_excludes_inactive_by_default(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.get(BASE)
    assert r.json() == []


async def test_get_list_include_inactive(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.get(BASE, params={"include_inactive": True})
    assert len(r.json()) == 1


async def test_update_returns_200_with_new_data(client: AsyncClient, saved: int) -> None:
    r = await client.patch(
        f"{BASE}/{saved}", json={"name": "ООО Василёк", "default_address": "пр. Мира, 5"}
    )
    assert r.status_code == 200
    assert r.json()["name"] == "ООО Василёк"


async def test_update_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(
        f"{BASE}/999", json={"name": "X", "default_address": "Y"}
    )
    assert r.status_code == 404


async def test_deactivate_returns_204(client: AsyncClient, saved: int) -> None:
    r = await client.post(f"{BASE}/{saved}/deactivate")
    assert r.status_code == 204


async def test_activate_returns_204(client: AsyncClient, saved: int) -> None:
    await client.post(f"{BASE}/{saved}/deactivate")
    r = await client.post(f"{BASE}/{saved}/activate")
    assert r.status_code == 204


async def test_deactivate_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(f"{BASE}/999/deactivate")
    assert r.status_code == 404
