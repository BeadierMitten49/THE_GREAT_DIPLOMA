from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from src.application.auth.exceptions import InvalidTokenError
from src.domain.auth.entities import User
from src.infrastructure.security.jwt_service import JWTService
from src.presentation.api.v1.auth.dependencies import get_current_user
from src.presentation.api.v1.dependencies import authenticated, director_only
from src.presentation.api.v1.notifications.dependencies import get_notification_service
from src.presentation.api.v1.notifications.schemas import NotificationResponse, UnreadCountResponse
from src.presentation.api.v1.notifications.service import NotificationService
from src.presentation.api.v1.notifications.ws_manager import manager

router = APIRouter(prefix="/notifications", tags=["Notifications"], dependencies=[authenticated])


def _to_response(n) -> NotificationResponse:
    return NotificationResponse(
        id=n.id,
        recipient_id=n.recipient_id,
        event_type=n.event_type,
        title=n.title,
        body=n.body,
        is_read=n.is_read,
        related_entity_type=n.related_entity_type,
        related_entity_id=n.related_entity_id,
        created_at=n.created_at,
    )


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    notifications = await service.get_my_notifications(user.id, unread_only=unread_only)
    return [_to_response(n) for n in notifications]


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    count = await service.get_unread_count(user.id)
    return UnreadCountResponse(count=count)


@router.get("/recent", response_model=list[NotificationResponse], dependencies=[director_only])
async def recent_notifications(
    limit: int = 20,
    service: NotificationService = Depends(get_notification_service),
):
    notifications = await service.get_recent(limit)
    return [_to_response(n) for n in notifications]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
):
    await service.mark_read(notification_id)
    return {"ok": True}


@router.post("/read-all")
async def mark_all_notifications_read(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    await service.mark_all_read(user.id)
    return {"ok": True}


@router.websocket("/ws")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)):
    """WebSocket for real-time notifications. Connect with ?token=<access_token>."""
    try:
        payload = JWTService().decode_access_token(token)
    except InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = int(payload["sub"])
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
