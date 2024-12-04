from typing import Any, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "SYN"

    # Database Settings
    DATABASE_URL: str
    DB_ECHO: bool = False

    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: List[str]

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: Optional[str]) -> Any:
        if not v:
            raise ValueError("Database URL must be provided")
        return v

    class Config:
        env_file = ".env"


# Create settings instance
settings = Settings()
