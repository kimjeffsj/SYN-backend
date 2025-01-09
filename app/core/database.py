from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

# Create DB Engine
engine = create_engine(
    settings.DATABASE_URL,
    # check connection
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
    connect_args={"options": "-c timezone=UTC"},
)

# Create Session
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
