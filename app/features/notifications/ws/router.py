import logging
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_user_from_token
from app.features.notifications.service import NotificationService
from app.features.notifications.ws_manager import notification_manager
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/notifications/{user_id}")
async def notification_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    db_session = None
    try:
        await websocket.accept()
        db_session = next(get_db())
        # get user from token
        user = await get_user_from_token(token, db_session)

        if not user or user.id != user_id:
            await websocket.close(code=4001)  # Unauthorized
            return

        # Connect WebSocket
        connected = await notification_manager.connect(user, websocket)
        if not connected:
            return

        try:
            # Send pending notifications
            pending_notifications = await NotificationService.get_pending_notifications(
                db_session, user_id
            )
            for notification in pending_notifications:
                await notification_manager.send_notification(
                    user_id, notification.to_dict()
                )

            # Handle incoming messages
            while True:
                data = await websocket.receive_text()
                await notification_manager.handle_message(user_id, data)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1011)
    finally:
        await notification_manager.disconnect(user_id)
        if db_session:
            db_session.close()


@router.get("/health")
async def websocket_health():
    """Health check endpoint for WebSocket service"""
    stats = notification_manager.get_connection_stats()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": stats,
    }
