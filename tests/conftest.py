"""Pytest configuration and fixtures"""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True)
def test_db():
    """Create a temporary test database for all tests."""
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = temp_db.name
    temp_db.close()
    
    # Override DB_PATH globally
    import app.config
    import app.db.sqlite
    
    original_db_path = app.config.DB_PATH
    app.config.DB_PATH = temp_db_path
    app.db.sqlite.DB_PATH = temp_db_path
    
    # Initialize the test database
    from app.db.sqlite import init_db
    init_db()
    
    yield temp_db_path
    
    # Cleanup
    app.config.DB_PATH = original_db_path
    app.db.sqlite.DB_PATH = original_db_path
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Clean up session storage before each test."""
    from app.agent.graph import _sessions
    _sessions.clear()
    yield
    _sessions.clear()
