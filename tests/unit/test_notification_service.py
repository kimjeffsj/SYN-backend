from datetime import datetime, timedelta

import pytest
from app.features.notifications.service import NotificationService
from app.models.notification import (
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


@pytest.fixture
def notification_data():
    """Basic notification data fixture"""
    return {
        "type": NotificationType.SCHEDULE_CHANGE,
        "title": "Schedule Update",
        "message": "Your schedule has been updated",
        "priority": NotificationPriority.NORMAL,
        "data": {"schedule_id": 1, "change": "time_update"},
    }


@pytest.mark.asyncio
async def test_create_notification(db_session, test_user, notification_data):
    """Test notification creation"""
    notification_data["user_id"] = test_user.id
    notification = await NotificationService.create_notification(
        db_session, notification_data
    )

    assert notification is not None
    assert notification.user_id == test_user.id
    assert notification.type == notification_data["type"]
    assert notification.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_get_user_notifications(db_session, test_user, notification_data):
    """Test retrieving user notifications"""
    # Create multiple notifications
    notification_data["user_id"] = test_user.id
    await NotificationService.create_notification(db_session, notification_data)

    high_priority_data = notification_data.copy()
    high_priority_data["priority"] = NotificationPriority.HIGH
    high_priority_data["title"] = "Urgent Update"
    await NotificationService.create_notification(db_session, high_priority_data)

    # Get notifications
    result = await NotificationService.get_user_notification(
        db_session, test_user.id, skip=0, limit=10
    )

    assert result["total"] == 2
    assert result["unread"] == 2
    assert len(result["items"]) == 2


@pytest.mark.asyncio
async def test_mark_notification_as_read(db_session, test_user, notification_data):
    """Test marking notification as read"""
    notification_data["user_id"] = test_user.id
    notification = await NotificationService.create_notification(
        db_session, notification_data
    )

    success = await NotificationService.mark_as_read(
        db_session, notification.id, test_user.id
    )

    assert success is True

    # Verify notification is marked as read
    result = await NotificationService.get_user_notification(db_session, test_user.id)
    assert result["unread"] == 0
    assert result["items"][0]["is_read"] is True


@pytest.mark.asyncio
async def test_mark_all_as_read(db_session, test_user, notification_data):
    """Test marking all notifications as read"""
    # Create multiple notifications
    notification_data["user_id"] = test_user.id
    await NotificationService.create_notification(db_session, notification_data)
    await NotificationService.create_notification(db_session, notification_data)

    success = await NotificationService.mark_all_as_read(db_session, test_user.id)
    assert success is True

    # Verify all notifications are read
    result = await NotificationService.get_user_notification(db_session, test_user.id)
    assert result["unread"] == 0


@pytest.mark.asyncio
async def test_get_pending_notifications(db_session, test_user, notification_data):
    """Test retrieving pending notifications"""
    # Create notifications with different dates
    notification_data["user_id"] = test_user.id
    await NotificationService.create_notification(db_session, notification_data)

    # Create an old notification
    old_notification = notification_data.copy()
    old_notification["created_at"] = datetime.now() - timedelta(days=20)
    await NotificationService.create_notification(db_session, old_notification)

    # Get pending notifications (default 15 days)
    notifications = await NotificationService.get_pending_notifications(
        db_session, test_user.id
    )

    assert len(notifications) == 1  # Only recent notification


@pytest.mark.asyncio
async def test_get_notification_summary(db_session, test_user, notification_data):
    """Test notification summary retrieval"""
    # Create notifications of different types
    notification_data["user_id"] = test_user.id
    await NotificationService.create_notification(db_session, notification_data)

    announcement_notification = notification_data.copy()
    announcement_notification["type"] = NotificationType.ANNOUNCEMENT
    await NotificationService.create_notification(db_session, announcement_notification)

    db_session.flush()

    summary = NotificationService.get_notification_summary(db_session, test_user.id)

    assert summary["total_unread"] == 2
    assert NotificationType.SCHEDULE_CHANGE.value in summary["type_summary"]
    assert NotificationType.ANNOUNCEMENT.value in summary["type_summary"]


@pytest.mark.asyncio
async def test_handle_user_login(db_session, test_user, notification_data):
    """Test notification handling during user login"""
    notification_data["user_id"] = test_user.id
    notification_data["priority"] = NotificationPriority.HIGH
    await NotificationService.create_notification(db_session, notification_data)

    login_data = await NotificationService.handle_user_login(db_session, test_user)

    assert len(login_data["notifications"]) == 1
    assert login_data["has_critical"] is True
    assert "summary" in login_data


@pytest.mark.asyncio
async def test_notification_websocket_connection(db_session, test_user):
    """Test WebSocket connection management"""
    from app.features.notifications.ws_manager import notification_manager
    from fastapi import WebSocket

    # Create a mock WebSocket
    class MockWebSocket:
        async def accept(self):
            pass

        async def send_json(self, data):
            pass

        async def close(self):
            pass

        client_state = "connected"

    websocket = MockWebSocket()

    # Test connection
    connected = await notification_manager.connect(test_user, websocket)
    assert connected is True

    # Test sending notification
    notification = {
        "type": NotificationType.SCHEDULE_CHANGE,
        "message": "Test notification",
    }
    sent = await notification_manager.send_notification(test_user.id, notification)
    assert sent is True

    # Test disconnection
    await notification_manager.disconnect(test_user.id)
    assert test_user.id not in notification_manager.active_connections
