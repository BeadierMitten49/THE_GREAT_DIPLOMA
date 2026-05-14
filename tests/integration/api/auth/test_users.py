import pytest

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_user(client, full_name: str = "Иванов Иван") -> int:
    resp = await client.post("/api/v1/users", json={"full_name": full_name, "password": "secret123"})
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


class TestAccessControl:
    async def test_get_users_requires_auth(self, client_no_auth):
        resp = await client_no_auth.get("/api/v1/users")
        assert resp.status_code == 401

    async def test_get_users_requires_director(self, client_warehouse):
        resp = await client_warehouse.get("/api/v1/users")
        assert resp.status_code == 403

    async def test_create_user_requires_director(self, client_warehouse):
        resp = await client_warehouse.post("/api/v1/users", json={"full_name": "Тест", "password": "pass123"})
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


class TestGetUsers:
    async def test_empty_list(self, client):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_created_user(self, client):
        await create_user(client)
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_inactive_excluded_by_default(self, client):
        user_id = await create_user(client)
        await client.post(f"/api/v1/users/{user_id}/deactivate")

        resp = await client.get("/api/v1/users")
        assert all(u["id"] != user_id for u in resp.json())

    async def test_include_inactive(self, client):
        user_id = await create_user(client)
        await client.post(f"/api/v1/users/{user_id}/deactivate")

        resp = await client.get("/api/v1/users?include_inactive=true")
        assert any(u["id"] == user_id for u in resp.json())


class TestGetUser:
    async def test_returns_user(self, client):
        user_id = await create_user(client, "Петров Пётр")
        resp = await client.get(f"/api/v1/users/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Петров Пётр"

    async def test_not_found_returns_404(self, client):
        resp = await client.get("/api/v1/users/999")
        assert resp.status_code == 404


class TestCreateUser:
    async def test_returns_201_with_id(self, client):
        resp = await client.post("/api/v1/users", json={"full_name": "Сидоров Сидор", "password": "pass123"})
        assert resp.status_code == 201
        assert "id" in resp.json()

    async def test_password_too_short_returns_422(self, client):
        resp = await client.post("/api/v1/users", json={"full_name": "Тест Тестов", "password": "123"})
        assert resp.status_code == 422


class TestUpdateUser:
    async def test_updates_full_name(self, client):
        user_id = await create_user(client)
        resp = await client.patch(f"/api/v1/users/{user_id}", json={"full_name": "Новое Имя"})
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Новое Имя"

    async def test_not_found_returns_404(self, client):
        resp = await client.patch("/api/v1/users/999", json={"full_name": "Кто-то"})
        assert resp.status_code == 404


class TestSetRoles:
    async def test_sets_roles(self, client):
        user_id = await create_user(client)
        resp = await client.post(f"/api/v1/users/{user_id}/roles", json={"roles": ["director", "warehouse"]})
        assert resp.status_code == 204


class TestDeactivateActivate:
    async def test_deactivate(self, client):
        user_id = await create_user(client)
        resp = await client.post(f"/api/v1/users/{user_id}/deactivate")
        assert resp.status_code == 204

    async def test_activate(self, client):
        user_id = await create_user(client)
        await client.post(f"/api/v1/users/{user_id}/deactivate")
        resp = await client.post(f"/api/v1/users/{user_id}/activate")
        assert resp.status_code == 204


class TestBindTelegram:
    async def test_binds_telegram(self, client):
        user_id = await create_user(client)
        resp = await client.post(f"/api/v1/users/{user_id}/bind-telegram", json={"telegram_username": "ivan_tg"})
        assert resp.status_code == 204


class TestResetPassword:
    async def test_resets_password(self, client):
        user_id = await create_user(client)
        resp = await client.post(
            f"/api/v1/users/{user_id}/reset-password",
            json={"old_password": "secret123", "new_password": "newpass123"},
        )
        assert resp.status_code == 204
