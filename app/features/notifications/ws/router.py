import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..ws_manager import notification_manager

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


@router.websocket("/notifications/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    db = SessionLocal()
    try:
        # WebSocket accept
        await websocket.accept()

        # Token validate
        params = dict(websocket.query_params)
        token = params.get("token")
        if not token:
            await websocket.close(code=4000)
            return

        # Auth user
        user = await get_user_from_token(token, db)
        if not user or str(user.id) != str(user_id):
            await websocket.close(code=4001)
            return

        # Keep Connection
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        db.close()


@router.websocket("/notifications/{user_id}")
async def notification_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    db = SessionLocal()
    try:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            email = payload.get("sub")
            if not email:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except JWTError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.error(f"User not found for email: {email}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if user.id != user_id:
            logger.error(
                f"User ID mismatch: token user {user.id} != requested {user_id}"
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        await notification_manager.connect(user_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                    continue

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")
        finally:
            await notification_manager.handle_disconnect(user_id)

    except Exception as e:
        logger.error(f"Error in WebSocket connection: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    finally:
        db.close()
