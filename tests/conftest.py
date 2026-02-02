import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.sqlite import init_db
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initialize the test database."""
    # Ensure we use a test database if possible, or just init the default one for now
    # In a real scenario, we might want to override the database path in app.config
    init_db()
    yield

@pytest.fixture
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as c:
        yield c
