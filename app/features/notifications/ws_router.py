import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .ws_manager import notification_manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_user_from_token(token: str, db: Session) -> User | None:
    """Validate token and return user"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if not email:
            return None

        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        return None


@router.websocket("/ws/notifications/{user_id}")
async def notification_websocket(
    websocket: WebSocket, user_id: int, token: str = Query(...)
):
    """WebSocket endpoint for real-time notifications"""

    # DB 세션 생성
    db = SessionLocal()
    try:
        # 토큰 검증 및 사용자 조회
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 사용자 ID 확인
        if user.id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # WebSocket 연결
        connection_successful = await notification_manager.connect(user_id, websocket)
        if not connection_successful:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    # Handle pong responses
                    if data == "pong":
                        continue

                    logger.debug(f"Received message from user {user_id}: {data}")

                except Exception as e:
                    logger.error(
                        f"Error processing message from user {user_id}: {str(e)}"
                    )

        except WebSocketDisconnect:
            await notification_manager.handle_disconnect(user_id)

        except Exception as e:
            logger.error(
                f"Unexpected error in websocket connection for user {user_id}: {str(e)}"
            )
            await notification_manager.handle_disconnect(user_id)

    finally:
        db.close()
