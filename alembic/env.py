"""Alembic environment using the same DATABASE_URL as the application."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import DATABASE_URL
from app.infrastructure.database import Base
import app.infrastructure.models  # noqa: F401 - registers mapped tables

config = context.config
database_url = config.attributes.get("database_url", DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata
CHECKPOINT_TABLES = {"checkpoints", "checkpoint_blobs", "checkpoint_writes", "checkpoint_migrations", "writes"}


def include_name(name, type_, parent_names):
    if type_ == "table" and name in CHECKPOINT_TABLES:
        return False
    return True


def run_migrations_offline():
    context.configure(url=database_url, target_metadata=target_metadata,
                      include_name=include_name, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          include_name=include_name, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
