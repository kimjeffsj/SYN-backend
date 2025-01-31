from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    blacklist_token,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
)
from app.models import User

from .schemas import LoginSchema, TokenSchema, UserCreateSchema, UserResponse
from .service import AuthService

router = APIRouter(tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    """Register a new user"""
    return AuthService.create_user(db, user_data)


@router.post("/login", response_model=TokenSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """Authenticate user and return tokens"""
    user = AuthService.authenticate_user(
        db, LoginSchema(email=form_data.username, password=form_data.password)
    )
    tokens = AuthService.create_user_tokens(user)

    response_data = TokenSchema(**tokens)
    response_data.redirect_url = (
        "/admin/dashboard" if user.role == "admin" else "/dashboard"
    )

    return TokenSchema(**tokens)


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)
):
    """Logout user and invalidate token"""
    blacklist_token(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user information"""
    return current_user
