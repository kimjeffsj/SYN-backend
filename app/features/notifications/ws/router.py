import json
import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import get_user_from_token
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .connection import WebSocketConnection
from .protocols import WSMessage, WSMessageType, WSProtocol

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/notifications/{user_id}")
async def notification_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    db = get_db()
    connection: Optional[WebSocketConnection] = None

    try:
        # Validate token and get user
        db_session = next(db)
        user = await get_user_from_token(token, db_session)

        if not user or user.id != user_id:
            await websocket.close(code=4001)  # Unauthorized
            return

        # Initialize connection and protocol
        connection = WebSocketConnection(websocket, user)
        protocol = WSProtocol(connection)

        # Establish connection
        await connection.connect()

        # Main message loop
        try:
            while True:
                data = await websocket.receive_text()
                await protocol.handle_message(data)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        if connection and connection.is_alive():
            await connection.handle_error(e)

    finally:
        if connection:
            await connection.disconnect()
        db_session.close()


@router.websocket("/events/{user_id}")
async def events_websocket(
    websocket: WebSocket,
    user_id: int,
    token: str = Query(...),
):
    db = get_db()
    connection: Optional[WebSocketConnection] = None

    try:
        # Validate token and get user
        db_session = next(db)
        user = await get_user_from_token(token, db_session)

        if not user or user.id != user_id:
            await websocket.close(code=4001)
            return

        # Initialize connection
        connection = WebSocketConnection(websocket, user)
        protocol = WSProtocol(connection)

        # Register event handlers
        # TODO: Add specific event handlers here

        # Establish connection
        await connection.connect()

        # Send initial state if needed
        welcome_message = WSMessage(
            type=WSMessageType.EVENT, payload={"message": "Connected to event stream"}
        )
        await protocol.send_message(welcome_message)

        # Main message loop
        try:
            while True:
                data = await websocket.receive_text()
                await protocol.handle_message(data)

        except WebSocketDisconnect:
            logger.info(f"Event WebSocket disconnected for user {user_id}")

    except Exception as e:
        logger.error(f"Event WebSocket error for user {user_id}: {str(e)}")
        if connection and connection.is_alive():
            await connection.handle_error(e)

    finally:
        if connection:
            await connection.disconnect()
        db_session.close()


@router.get("/health")
async def websocket_health():
    """Health check endpoint for WebSocket service"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
