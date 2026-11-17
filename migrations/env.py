"""Alembic environment.

The database URL comes from ``DATABASE_URL`` (via ``apps.api.settings.Settings``),
never from a config file. Target metadata is the complete application metadata
assembled in ``apps.api.tables``.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api.settings import Settings
from apps.api.tables import metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = metadata


def _database_url() -> str:
    # An explicit URL set programmatically (tests) wins over the environment.
    override = config.attributes.get("database_url")
    if isinstance(override, str) and override:
        return override
    return Settings().database_url.get_secret_value()


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting (``alembic upgrade head --sql``)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(_database_url(), poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
