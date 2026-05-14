from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from src.application.auth.exceptions import InvalidTokenError
from src.application.ports.auth import IJWTService
from src.infrastructure.config import settings


class JWTService(IJWTService):
    def create_access_token(self, user_id: int, roles: list[str]) -> str:
        payload = {
            "sub": str(user_id),
            "roles": roles,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_ttl_minutes),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    def decode_access_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except ExpiredSignatureError:
            raise InvalidTokenError("access token expired")
        except JWTError:
            raise InvalidTokenError()
