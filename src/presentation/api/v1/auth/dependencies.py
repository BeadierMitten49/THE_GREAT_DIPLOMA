from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.exceptions import InvalidTokenError
from src.domain.auth.entities import User
from src.domain.auth.value_objects import Role
from src.infrastructure.db.repositories.auth import UserRepository
from src.infrastructure.db.session import get_session
from src.infrastructure.security.jwt_service import JWTService
from src.presentation.api.v1.auth.service import AuthService, UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session)


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = JWTService().decode_access_token(token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found or deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: Role):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not any(current_user.has_role(r) for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient permissions",
            )
        return current_user

    return dependency
