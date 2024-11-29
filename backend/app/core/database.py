from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# Create DB Engine
engine = create_engine(
    settings.DATABASE_URL,
    # check connection
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
)

# Create Session
SessionLocal = sessionmaker(bind=engine)


# Base Model Class
class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
