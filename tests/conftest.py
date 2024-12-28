import pytest
from app.core.database import get_db
from app.models.base import Base
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/syn_test"


@pytest.fixture(scope="session")
def test_engine():
    """Create test db engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create new db session for a test"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()

    # Delete all data from all tables before each test
    Base.metadata.create_all(bind=test_engine)
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module")
def client():
    """Create test client"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    from app.core.security import get_password_hash
    from app.models.user import User

    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role="employee",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
