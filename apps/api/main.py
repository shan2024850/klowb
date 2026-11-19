"""FastAPI composition root.

Run with::

    uv run uvicorn apps.api.main:create_app --factory --port 8000

``create_app`` accepts substitutes for every external collaborator so tests can
build isolated applications.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.deps import Container
from apps.api.errors import register_exception_handlers
from apps.api.middleware import (
    ErrorBoundaryMiddleware,
    RequestMetricsMiddleware,
    SecurityHeadersMiddleware,
)
from apps.api.routers import health, system
from apps.api.settings import Settings
from libs.domain.clock import Clock, SystemClock
from libs.observability.correlation import HEADER_NAME, CorrelationIdMiddleware
from libs.observability.logging import configure_logging, get_logger
from libs.observability.metrics import Metrics
from libs.storage.cache import Cache
from libs.storage.database import Database

API_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    *,
    clock: Clock | None = None,
    metrics: Metrics | None = None,
    configure_logs: bool = True,
) -> FastAPI:
    # Loading settings validates the trading-safety gates; a refused configuration
    # raises here and the process does not start.
    settings = settings if settings is not None else Settings()
    if configure_logs:
        configure_logging(settings.log_level, json_output=settings.log_format == "json")
    log = get_logger(__name__)

    clock = clock if clock is not None else SystemClock()
    metrics = metrics if metrics is not None else Metrics()
    timeout = settings.dependency_check_timeout_seconds
    database = Database(settings.database_url.get_secret_value(), connect_timeout_seconds=timeout)
    cache = (
        Cache(settings.redis_url.get_secret_value(), connect_timeout_seconds=timeout)
        if settings.redis_enabled
        else None
    )
    container = Container(
        settings=settings, clock=clock, metrics=metrics, database=database, cache=cache
    )
    metrics.app_info.labels(
        settings.app_version, settings.app_env.value, settings.trading_mode.value
    ).set(1)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        log.info(
            "application_startup",
            version=settings.app_version,
            environment=settings.app_env.value,
            trading_mode=settings.trading_mode.value,
            redis_enabled=settings.redis_enabled,
            llm_enabled=settings.llm_enabled,
        )
        try:
            yield
        finally:
            if cache is not None:
                await cache.close()
            await database.dispose()
            log.info("application_shutdown")

    app = FastAPI(
        title="klowb API",
        version=settings.app_version,
        summary="Quantitative research and trading platform API. Research mode by default.",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.container = container

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(system.router, prefix=API_PREFIX)

    # Middleware added last is outermost. Resulting order (outermost first):
    # CorrelationId -> SecurityHeaders -> RequestMetrics -> ErrorBoundary -> [CORS] -> app
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["content-type", "x-csrf-token", HEADER_NAME],
            expose_headers=[HEADER_NAME],
            max_age=600,
        )
    app.add_middleware(ErrorBoundaryMiddleware, metrics=metrics)
    app.add_middleware(RequestMetricsMiddleware, metrics=metrics)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    return app
