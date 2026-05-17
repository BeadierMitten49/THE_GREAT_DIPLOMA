import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE = "/api/v1/orders"


# ---------------------------------------------------------------------------
# GET /orders
# ---------------------------------------------------------------------------


async def test_get_orders_empty(client: AsyncClient) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert r.json() == []


async def test_get_orders_returns_list(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.get(BASE)
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_get_orders_filter_by_status(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.get(BASE, params={"status": "created"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"status": "production"})
    assert r.status_code == 200
    assert len(r.json()) == 0


async def test_get_orders_filter_by_customer(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.get(BASE, params={"customer_id": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = await client.get(BASE, params={"customer_id": 999})
    assert r.status_code == 200
    assert len(r.json()) == 0


# ---------------------------------------------------------------------------
# GET /orders/{id}
# ---------------------------------------------------------------------------


async def test_get_order_returns_200(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.get(f"{BASE}/{saved_order_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == saved_order_id
    assert data["number"] == 1
    assert data["customer_id"] == 1
    assert data["status"] == "created"


async def test_get_order_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.get(f"{BASE}/999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /orders/{id}/items
# ---------------------------------------------------------------------------


async def test_get_order_items(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.get(f"{BASE}/{saved_order_id}/items")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["product_id"] == 1
    assert items[0]["quantity"] == 100


# ---------------------------------------------------------------------------
# POST /orders
# ---------------------------------------------------------------------------


async def test_create_order_returns_201(client: AsyncClient) -> None:
    r = await client.post(BASE, json={
        "customer_id": 1,
        "delivery_address": "ул. Пушкина, 1",
        "delivery_date": "2026-06-01",
        "items": [{"product_id": 1, "quantity": 50}],
    })
    assert r.status_code == 201
    assert "id" in r.json()


async def test_create_order_missing_field_returns_422(client: AsyncClient) -> None:
    r = await client.post(BASE, json={"customer_id": 1})
    assert r.status_code == 422


async def test_create_order_number_increments(client: AsyncClient) -> None:
    r1 = await client.post(BASE, json={
        "customer_id": 1, "delivery_address": "a",
        "delivery_date": "2026-06-01", "items": [{"product_id": 1, "quantity": 10}],
    })
    r2 = await client.post(BASE, json={
        "customer_id": 1, "delivery_address": "b",
        "delivery_date": "2026-06-01", "items": [{"product_id": 1, "quantity": 10}],
    })
    id1, id2 = r1.json()["id"], r2.json()["id"]
    n1 = (await client.get(f"{BASE}/{id1}")).json()["number"]
    n2 = (await client.get(f"{BASE}/{id2}")).json()["number"]
    assert n2 == n1 + 1


# ---------------------------------------------------------------------------
# PATCH /orders/{id}/status
# ---------------------------------------------------------------------------


async def test_change_status_returns_204(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.patch(
        f"{BASE}/{saved_order_id}/status", json={"new_status": "production"}
    )
    assert r.status_code == 204


async def test_change_status_invalid_transition_returns_422(
    client: AsyncClient, saved_order_id: int
) -> None:
    r = await client.patch(
        f"{BASE}/{saved_order_id}/status", json={"new_status": "completed"}
    )
    assert r.status_code == 422


async def test_change_status_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.patch(f"{BASE}/999/status", json={"new_status": "production"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PUT /orders/{id}
# ---------------------------------------------------------------------------


async def test_edit_order_returns_204(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.put(f"{BASE}/{saved_order_id}", json={
        "delivery_address": "ул. Лермонтова, 5",
        "delivery_date": "2026-07-01",
        "items": [{"product_id": 2, "quantity": 30}],
    })
    assert r.status_code == 204


async def test_edit_order_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.put(f"{BASE}/999", json={
        "delivery_address": "a", "delivery_date": "2026-06-01", "items": [],
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /orders/{id}
# ---------------------------------------------------------------------------


async def test_delete_order_returns_204(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.delete(f"{BASE}/{saved_order_id}")
    assert r.status_code == 204


async def test_delete_order_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.delete(f"{BASE}/999")
    assert r.status_code == 404


async def test_deleted_order_excluded_from_list(client: AsyncClient, saved_order_id: int) -> None:
    await client.delete(f"{BASE}/{saved_order_id}")
    r = await client.get(BASE)
    assert r.json() == []


# ---------------------------------------------------------------------------
# POST /orders/{id}/reservations
# ---------------------------------------------------------------------------


async def test_reserve_product_returns_201(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.post(
        f"{BASE}/{saved_order_id}/reservations", json={"stock_id": 1, "quantity": 50}
    )
    assert r.status_code == 201
    assert "id" in r.json()


async def test_reserve_product_order_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.post(
        f"{BASE}/999/reservations", json={"stock_id": 1, "quantity": 50}
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /orders/reservation/{reservation_id}
# ---------------------------------------------------------------------------


async def test_release_reservation_returns_204(client: AsyncClient, saved_order_id: int) -> None:
    r = await client.post(
        f"{BASE}/{saved_order_id}/reservations", json={"stock_id": 1, "quantity": 50}
    )
    rid = r.json()["id"]
    r = await client.delete(f"{BASE}/reservation/{rid}")
    assert r.status_code == 204


async def test_release_reservation_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.delete(f"{BASE}/reservation/999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /orders/{id}/reservations
# ---------------------------------------------------------------------------


async def test_release_all_reservations_returns_204(
    client: AsyncClient, saved_order_id: int
) -> None:
    await client.post(
        f"{BASE}/{saved_order_id}/reservations", json={"stock_id": 1, "quantity": 50}
    )
    r = await client.delete(f"{BASE}/{saved_order_id}/reservations")
    assert r.status_code == 204


async def test_release_all_reservations_not_found_returns_404(client: AsyncClient) -> None:
    r = await client.delete(f"{BASE}/999/reservations")
    assert r.status_code == 404
