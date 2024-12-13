from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend.app.core.security import get_current_user
from backend.app.models.user import User

from .ws_manager import notification_manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def notification_websocket(
    websocket: WebSocket, user_id: int, current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        await websocket.close(code=4003)
        return

    await notification_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        notification_manager.disconnect(user_id)
