from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from src.application.auth.exceptions import InvalidTokenError
from src.infrastructure.config import settings
from src.infrastructure.security.jwt_service import JWTService
from src.infrastructure.security.password_hasher import BcryptPasswordHasher

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# BcryptPasswordHasher
# ---------------------------------------------------------------------------


class TestBcryptPasswordHasher:
    def test_hash_returns_string(self):
        hasher = BcryptPasswordHasher()
        assert isinstance(hasher.hash("secret"), str)

    def test_verify_correct_password(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("secret")
        assert hasher.verify("secret", hashed) is True

    def test_verify_wrong_password(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("secret")
        assert hasher.verify("wrong", hashed) is False

    def test_hash_is_unique_each_time(self):
        hasher = BcryptPasswordHasher()
        assert hasher.hash("secret") != hasher.hash("secret")


# ---------------------------------------------------------------------------
# JWTService
# ---------------------------------------------------------------------------


class TestJWTService:
    def test_create_and_decode(self):
        svc = JWTService()
        token = svc.create_access_token(user_id=1, roles=["director"])
        payload = svc.decode_access_token(token)
        assert payload["sub"] == "1"
        assert payload["roles"] == ["director"]

    def test_decode_multiple_roles(self):
        svc = JWTService()
        token = svc.create_access_token(user_id=5, roles=["warehouse", "production"])
        payload = svc.decode_access_token(token)
        assert set(payload["roles"]) == {"warehouse", "production"}

    def test_decode_invalid_token_raises(self):
        svc = JWTService()
        with pytest.raises(InvalidTokenError):
            svc.decode_access_token("invalid.token.here")

    def test_decode_expired_token_raises(self):
        svc = JWTService()
        payload = {
            "sub": "1",
            "roles": [],
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        with pytest.raises(InvalidTokenError) as exc_info:
            svc.decode_access_token(expired)
        assert "expired" in str(exc_info.value)

    def test_decode_wrong_secret_raises(self):
        svc = JWTService()
        payload = {"sub": "1", "roles": [], "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
        token = jwt.encode(payload, "wrong_secret", algorithm=settings.algorithm)
        with pytest.raises(InvalidTokenError):
            svc.decode_access_token(token)
