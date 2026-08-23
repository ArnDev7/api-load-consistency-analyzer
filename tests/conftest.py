import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_session_factory, get_engine
from app.dependencies import get_db
from app.main import app
from app.models import Base, Item, Reservation, ReservationStatus


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema exists before tests run."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide clean database session per test function."""
    session_factory = get_session_factory()
    session = session_factory()
    # Clean tables
    session.execute(text("TRUNCATE TABLE reservations, items RESTART IDENTITY CASCADE"))
    session.commit()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide FastAPI test client with overridden db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_item(db_session: Session) -> Item:
    """Fixture providing a standard test inventory item."""
    item = Item(
        sku="SKU-TEST-001",
        name="Test Inventory Widget",
        available_quantity=100,
        initial_quantity=100,
        version=1,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item
