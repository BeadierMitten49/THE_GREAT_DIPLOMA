from fastapi import APIRouter, Depends, HTTPException, status

from src.application.auth.exceptions import AuthenticationError, DeactivatedUserError, InvalidTokenError, RateLimitError
from src.presentation.api.v1.auth.dependencies import get_auth_service
from src.presentation.api.v1.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from src.presentation.api.v1.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = await service.login(body.username, body.password)
    except RateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except DeactivatedUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = await service.refresh_tokens(body.refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=result.access_token, refresh_token=result.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    await service.logout(body.refresh_token)
