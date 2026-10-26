from alembic import command
from alembic.config import Config
from sqlalchemy.engine import URL

from app.infrastructure.checkpoints import open_checkpointer


def test_sqlite_migration_ignores_langgraph_checkpoint_tables(tmp_path):
    url = URL.create("sqlite+pysqlite", database=str(tmp_path / "medagenda.sqlite")).render_as_string()
    migration = Config("alembic.ini")
    migration.attributes["database_url"] = url
    command.upgrade(migration, "head")

    with open_checkpointer(url) as checkpointer:
        checkpointer.get_tuple({"configurable": {"thread_id": "smoke"}})

    command.check(migration)
