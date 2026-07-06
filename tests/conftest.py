"""
conftest.py
-----------
Shared pytest fixtures.

The key idea: we do NOT want the test suite to touch the real ``maintenance.db``
file. Instead we spin up a separate, isolated SQLite database for the tests and
override the ``get_db`` dependency so the application uses it. This demonstrates
one of the biggest practical benefits of dependency injection -- swapping the
database out for tests without changing a single line of application code.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# A dedicated in-memory SQLite database for tests. ``StaticPool`` keeps a single
# shared connection alive so the in-memory schema persists across the requests
# made within one test.
TEST_ENGINE = create_engine(
    "sqlite://",  # in-memory
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=TEST_ENGINE
)


def _override_get_db():
    """Test replacement for the ``get_db`` dependency."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """Yield a TestClient backed by a fresh, empty database for each test."""
    # Create all tables on the test engine, then wire the override in.
    Base.metadata.create_all(bind=TEST_ENGINE)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Tear down: drop everything and remove the override so tests stay isolated.
    Base.metadata.drop_all(bind=TEST_ENGINE)
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_machine_payload() -> dict:
    """A valid machine creation payload reused across tests."""
    return {
        "name": "CNC Lathe #4",
        "department": "Machining",
        "manufacturer": "Siemens",
        "installation_date": "2022-05-14",
        "operating_hours": 1200.5,
        "health_score": 85.0,
        "status": "Running",
    }
