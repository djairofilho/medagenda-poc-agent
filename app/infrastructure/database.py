"""SQLAlchemy engine and dialect-specific statements for supported databases."""

from datetime import datetime, timezone

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_session_factory(database_url: str):
    driver = make_url(database_url).drivername
    if driver == "postgresql+psycopg":
        engine = create_engine(database_url, pool_pre_ping=True)
    elif driver in ("sqlite", "sqlite+pysqlite"):
        engine = create_engine(database_url, connect_args={"timeout": 30, "check_same_thread": False})

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        if make_url(database_url).database != ":memory:":
            with engine.connect() as connection:
                connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    else:
        raise ValueError("DATABASE_URL must use postgresql+psycopg or sqlite")
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def dialect_insert(session, model):
    """Return an upsert-capable INSERT for the active SQLAlchemy dialect."""
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        return postgres_insert(model)
    if dialect == "sqlite":
        return sqlite_insert(model)
    raise ValueError(f"Unsupported database dialect: {dialect}")


def lock_sqlite_writer(session) -> None:
    """Serialize SQLite booking transactions before reading an idempotency key."""
    if session.get_bind().dialect.name == "sqlite":
        session.execute(text("BEGIN IMMEDIATE"))


def utc_isoformat(value: datetime) -> str:
    """Restore the UTC offset that SQLite omits when reading timestamps."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()
