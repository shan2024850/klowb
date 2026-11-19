"""PostgreSQL access (SQLAlchemy async + asyncpg)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Owns the engine and session factory. One instance per application."""

    def __init__(
        self,
        url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 5,
        connect_timeout_seconds: float = 5.0,
        echo: bool = False,
    ) -> None:
        self._engine: AsyncEngine = create_async_engine(
            url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            connect_args={"timeout": connect_timeout_seconds},
        )
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Transactional scope: commit on success, roll back on error."""
        async with self._sessions() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    async def ping(self, timeout_seconds: float) -> None:
        """Raise if the database does not answer ``SELECT 1`` within the timeout."""
        async with asyncio.timeout(timeout_seconds):
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self._engine.dispose()
