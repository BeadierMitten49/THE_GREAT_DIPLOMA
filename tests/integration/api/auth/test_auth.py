import pytest

pytestmark = pytest.mark.integration


class TestLogin:
    async def test_success_returns_tokens(self, client):
        resp = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_wrong_password_returns_401(self, client):
        resp = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "wrong"})
        assert resp.status_code == 401

    async def test_unknown_user_returns_401(self, client):
        resp = await client.post("/api/v1/auth/login", json={"username": "nobody", "password": "secret123"})
        assert resp.status_code == 401

    async def test_rate_limited_returns_429(self, client):
        for _ in range(5):
            await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "wrong"})
        resp = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        assert resp.status_code == 429


class TestRefresh:
    async def test_success_returns_new_tokens(self, client):
        login = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["refresh_token"] != refresh_token

    async def test_invalid_token_returns_401(self, client):
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
        assert resp.status_code == 401

    async def test_reuse_revoked_token_returns_401(self, client):
        login = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        refresh_token = login.json()["refresh_token"]
        await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401


class TestLogout:
    async def test_success_returns_204(self, client):
        login = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 204

    async def test_after_logout_refresh_returns_401(self, client):
        login = await client.post("/api/v1/auth/login", json={"username": "ivanov_ivan", "password": "secret123"})
        refresh_token = login.json()["refresh_token"]
        await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401
