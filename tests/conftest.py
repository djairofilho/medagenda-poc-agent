"""Isolated PostgreSQL and SQLite databases for integration tests."""

from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app import config
from app.main import create_app
from app.evals.fake_model import FakeModel


@pytest.fixture(params=["postgresql", "sqlite"], ids=["postgresql", "sqlite"])
def app_factory(request, tmp_path):
    if request.param == "sqlite":
        test_url = URL.create("sqlite+pysqlite", database=str(tmp_path / "medagenda.sqlite")).render_as_string()
        migration = Config("alembic.ini")
        migration.attributes["database_url"] = test_url
        command.upgrade(migration, "head")

        def factory(model=None, tracer=None):
            return create_app(database_url=test_url, checkpoint_url=test_url,
                              model=model or FakeModel(), tracer=tracer)

        yield factory
        return

    source = make_url(config.DATABASE_URL)
    if source.host not in ("localhost", "127.0.0.1"):
        pytest.skip("Integration tests require the local PostgreSQL Compose service")
    name = f"medagenda_test_{uuid4().hex[:12]}"
    admin = create_engine(source.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    test_url = source.set(database=name).render_as_string(hide_password=False)
    checkpoint_url = test_url.replace("postgresql+psycopg://", "postgresql://")
    migration = Config("alembic.ini")
    migration.attributes["database_url"] = test_url
    command.upgrade(migration, "head")

    def factory(model=None, tracer=None):
        return create_app(database_url=test_url, checkpoint_url=checkpoint_url,
                          model=model or FakeModel(), tracer=tracer)

    yield factory
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def client(app_factory):
    with TestClient(app_factory()) as test_client:
        yield test_client
