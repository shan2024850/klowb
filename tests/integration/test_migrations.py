from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api.settings import Settings
from apps.api.tables import metadata

pytestmark = pytest.mark.integration


def round_trip(connection: Connection) -> None:
    config = Config(
        toml_file=Path(__file__).resolve().parents[2] / "pyproject.toml",
        attributes={"connection": connection},
    )
    schema = "migration_" + uuid4().hex
    connection.exec_driver_sql(f"CREATE SCHEMA {schema}")
    connection.exec_driver_sql(f"SET LOCAL search_path TO {schema}")

    def tables() -> set[str]:
        return set(
            connection.exec_driver_sql(
                "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
            ).scalars()
        )

    expected = set(metadata.tables) | {"alembic_version"}
    assert tables() == set()
    command.upgrade(config, "head")
    assert tables() == expected
    command.downgrade(config, "base")
    assert tables() == {"alembic_version"}
    command.upgrade(config, "head")
    assert tables() == expected


async def test_p1_int_003_migration_round_trip(settings: Settings) -> None:
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            # Run all DDL inside an outer transaction, rolled back on close.
            await connection.begin()
            await connection.run_sync(round_trip)
    finally:
        await engine.dispose()
