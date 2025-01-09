import pytest
from app.features.auth.schemas import LoginSchema
from app.features.auth.service import AuthService
from fastapi import HTTPException


# Authenticate user tests
def test_authenticate_user_success(db_session, test_user):
    """Test successful user authentication"""
    login_data = LoginSchema(email="test@example.com", password="testpass123")

    user = AuthService.authenticate_user(db_session, login_data)

    assert user is not None
    assert user.email == "test@example.com"
    assert user.role == "employee"


# Wrong password test
def test_authenticate_user_wrong_password(db_session, test_user):
    """Test user authentication with wrong password"""
    login_data = LoginSchema(email="test@example.com", password="wrongpass123")

    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(db_session, login_data)

    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in str(exc_info.value.detail)


# Non-existent email test
def test_authenticate_user_nonexistent_email(db_session, test_user):
    """Test user authentication with non-existent email"""
    login_data = LoginSchema(email="not-exist@example.com", password="testpass123")

    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(db_session, login_data)

    assert exc_info.value.status_code == 401
    assert "Incorrect email or password" in str(exc_info.value.detail)


# Create access token test
def test_authenticate_create_user_tokens(db_session, test_user):
    """Test creating access token"""
    tokens = AuthService.create_user_tokens(test_user)

    assert isinstance(tokens, dict)
    assert len(tokens) > 0


# Get user by email tests
def test_authenticate_get_user_by_email(db_session, test_user):
    """Test getting user by email"""
    user = AuthService.get_user_by_email(db_session, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"


def test_get_user_by_email_not_found(db_session):
    """Test getting user by email - not found case"""
    user = AuthService.get_user_by_email(db_session, "nonexistent@example.com")
    assert user is None


def test_get_user_by_email_invalid(db_session):
    """Test getting user by email - invalid email"""
    user = AuthService.get_user_by_email(db_session, None)
    assert user is None
