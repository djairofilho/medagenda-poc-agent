"""Select a LangGraph checkpointer from a database URL."""

from contextlib import contextmanager

from sqlalchemy.engine import make_url


@contextmanager
def open_checkpointer(database_url: str):
    parsed = make_url(database_url)
    if parsed.drivername.startswith("postgresql"):
        from langgraph.checkpoint.postgres import PostgresSaver

        connection_url = parsed.set(drivername="postgresql").render_as_string(hide_password=False)
        with PostgresSaver.from_conn_string(connection_url) as saver:
            saver.setup()
            yield saver
    elif parsed.drivername in ("sqlite", "sqlite+pysqlite"):
        from langgraph.checkpoint.sqlite import SqliteSaver

        if not parsed.database or parsed.database == ":memory:":
            raise ValueError("SQLite checkpoints require a file-backed database URL")
        with SqliteSaver.from_conn_string(parsed.database) as saver:
            yield saver
    else:
        raise ValueError("CHECKPOINT_DATABASE_URL must use PostgreSQL or SQLite")
