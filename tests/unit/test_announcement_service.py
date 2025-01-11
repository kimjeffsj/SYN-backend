import pytest
from app.features.announcements.schemas import AnnouncementCreate, AnnouncementUpdate
from app.features.announcements.service import AnnouncementService
from fastapi import HTTPException


@pytest.fixture
def announcement_data():
    """Fixture for basic announcement data"""
    return {
        "title": "Test Announcement",
        "content": "This is a test announcement",
        "priority": "normal",
    }


@pytest.fixture
def create_announcement(db_session, test_admin, announcement_data):
    """Fixture for create a test announcement"""

    async def _create_announcement():
        return await AnnouncementService.create_announcement(
            db=db_session,
            announcement_data=AnnouncementCreate(**announcement_data),
            created_by=test_admin.id,
        )

    return _create_announcement


@pytest.mark.asyncio
async def test_create_announcement(db_session, test_admin, announcement_data):
    """Test creating a new announcement"""
    announcement = await AnnouncementService.create_announcement(
        db=db_session,
        announcement_data=AnnouncementCreate(**announcement_data),
        created_by=test_admin.id,
    )

    assert announcement["title"] == announcement_data["title"]
    assert announcement["content"] == announcement_data["content"]
    assert announcement["priority"] == announcement_data["priority"]
    assert announcement["created_by"] == test_admin.id
    assert announcement["read_count"] == 0


@pytest.mark.asyncio
async def test_get_announcements(
    db_session, test_admin, test_user, create_announcement
):
    """Test getting announcements with various filters"""
    # Create test announcements
    announcement1 = await create_announcement()

    # Create high priority announcement
    high_priority_data = {
        "title": "Urgent Notice",
        "content": "High priority announcement",
        "priority": "high",
    }
    announcement2 = await AnnouncementService.create_announcement(
        db=db_session,
        announcement_data=AnnouncementCreate(**high_priority_data),
        created_by=test_admin.id,
    )

    # Test getting all announcements
    result = await AnnouncementService.get_announcements(
        db=db_session, user_id=test_user.id, skip=0, limit=10
    )

    assert result["total"] == 2
    assert result["unread"] == 2
    assert len(result["items"]) == 2

    # Test filtering by priority
    high_priority_results = await AnnouncementService.get_announcements(
        db=db_session, user_id=test_user.id, skip=0, limit=10, priority="high"
    )

    assert len(high_priority_results["items"]) == 1
    assert high_priority_results["items"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_mark_announcement_as_read(
    db_session, test_admin, test_user, create_announcement
):
    """Test marking announcements as read"""
    announcement = await create_announcement()

    # Mark as read
    success = await AnnouncementService.mark_as_read(
        db=db_session, announcement_id=announcement["id"], user_id=test_user.id
    )

    assert success is True

    # Verify read status
    result = await AnnouncementService.get_announcements(
        db=db_session, user_id=test_user.id, skip=0, limit=10
    )

    assert result["unread"] == 0
    assert result["items"][0]["is_read"] is True


@pytest.mark.asyncio
async def test_update_announcement(db_session, test_admin, create_announcement):
    """Test updating announcement"""
    announcement = await create_announcement()

    update_data = AnnouncementUpdate(
        title="Updated Title", content="Updated content", priority="high"
    )

    updated = await AnnouncementService.update_announcement(
        db=db_session, announcement_id=announcement["id"], update_data=update_data
    )

    assert updated["title"] == "Updated Title"
    assert updated["content"] == "Updated content"
    assert updated["priority"] == "high"


@pytest.mark.asyncio
async def test_delete_announcement(db_session, test_admin, create_announcement):
    """Test soft deleting announcement"""
    announcement = await create_announcement()

    success = await AnnouncementService.delete_announcement(
        db=db_session, announcement_id=announcement["id"]
    )

    assert success is True

    # Verify announcement is not returned in queries
    result = await AnnouncementService.get_announcements(
        db=db_session, user_id=test_admin.id, skip=0, limit=10
    )

    assert len(result["items"]) == 0


@pytest.mark.asyncio
async def test_search_announcements(db_session, test_admin, test_user):
    """Test searching announcements"""
    # Create test announcements with different content
    announcements_data = [
        {
            "title": "Project Update",
            "content": "New project timeline",
            "priority": "normal",
        },
        {
            "title": "Holiday Notice",
            "content": "Office closure dates",
            "priority": "high",
        },
    ]

    for data in announcements_data:
        await AnnouncementService.create_announcement(
            db=db_session,
            announcement_data=AnnouncementCreate(**data),
            created_by=test_admin.id,
        )

    # Test search functionality
    search_results = await AnnouncementService.get_announcements(
        db=db_session, user_id=test_user.id, skip=0, limit=10, search="project"
    )

    assert len(search_results["items"]) == 1
    assert "Project" in search_results["items"][0]["title"]


@pytest.mark.asyncio
async def test_error_handling(db_session, test_admin):
    """Test error handling in announcement operations"""
    # Test creating announcement with invalid data
    invalid_data = {
        "title": "",  # Empty title
        "content": "Test content",
        "priority": "invalid_priority",  # Invalid priority
    }

    with pytest.raises(HTTPException) as exc_info:
        await AnnouncementService.create_announcement(
            db=db_session,
            announcement_data=AnnouncementCreate(**invalid_data),
            created_by=test_admin.id,
        )

    assert exc_info.value.status_code == 400

    # Test updating non-existent announcement
    update_data = AnnouncementUpdate(
        title="Updated Title", content="Updated content", priority="normal"
    )

    with pytest.raises(HTTPException) as exc_info:
        await AnnouncementService.update_announcement(
            db=db_session,
            announcement_id=99999,  # Non-existent ID
            update_data=update_data,
        )

    assert exc_info.value.status_code == 404
