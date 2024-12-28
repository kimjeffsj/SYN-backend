import pytest
from app.features.auth.schemas import LoginSchema
from app.features.auth.service import AuthService
from fastapi import HTTPException


def test_authenticate_user_success(db_session, test_user):
    """Test successful user authentication"""
    login_data = LoginSchema(email="test@example.com", password="testpass123")

    user = AuthService.authenticate_user(db_session, login_data)

    assert user is not None
    assert user.email == "test@example.com"
    assert user.role == "employee"


def test_authenticate_user_wrong_password(db_session, test_user):
    """Test user authentication with wrong password"""
    login_data = LoginSchema(email="test@example.com", password="wrongpass123")

    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(db_session, login_data)

    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in str(exc_info.value.detail)
