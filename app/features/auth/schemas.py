from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserCreateSchema(BaseModel):
    """Schema for creating a new user"""

    email: EmailStr
    full_name: str
    password: str
    role: str = "employee"  # Default role is employee

    @field_validator("email")
    def email_to_lowercase(cls, v: str) -> str:
        return v.lower()


class UserResponse(BaseModel):
    """Schema for user response"""

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    """Schema for JWT token"""

    access_token: str
    token_type: str
    redirect_url: Optional[str] = None


class TokenDataSchema(BaseModel):
    """Schema for JWT token data"""

    email: Optional[str] = None


class LoginSchema(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str
