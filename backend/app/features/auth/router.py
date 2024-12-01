from typing import Annotated

from app.core.database import get_db
from app.core.security import get_current_active_user, get_current_user, oauth2_scheme
from app.models import User
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .schemas import LoginSchema, TokenSchema, UserCreateSchema, UserResponse
from .service import AuthService

router = APIRouter()


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
    return TokenSchema(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user information"""
    return current_user
