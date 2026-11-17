"""Dependency health checks used by the readiness endpoint."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

from libs.domain.clock import Clock
from libs.domain.enums import DependencyStatus, ReadinessStatus
from libs.observability.logging import get_logger
from libs.observability.metrics import Metrics
from libs.schemas.system import DependencyHealth, ReadinessReport
from libs.storage.cache import Cache
from libs.storage.database import Database

log = get_logger(__name__)

Ping = Callable[[float], Awaitable[None]]


async def check_dependency(
    name: str, ping: Ping, *, required: bool, timeout_seconds: float, metrics: Metrics
) -> DependencyHealth:
    """Run one bounded health check. Never raises."""
    started = time.perf_counter()
    try:
        # The ping enforces its own timeout; this outer bound guarantees it.
        async with asyncio.timeout(timeout_seconds + 0.5):
            await ping(timeout_seconds)
    except Exception as exc:  # noqa: BLE001 - a health check must report any failure
        elapsed = time.perf_counter() - started
        metrics.dependency_up.labels(name).set(0)
        metrics.dependency_check_duration_seconds.labels(name).set(elapsed)
        log.warning(
            "dependency_check_failed",
            dependency=name,
            required=required,
            error_type=type(exc).__name__,
            error=str(exc),
            duration_ms=round(elapsed * 1000, 3),
        )
        # Only the error class is exposed; messages can contain connection details.
        return DependencyHealth(
            name=name,
            status=DependencyStatus.DOWN,
            required=required,
            latency_ms=round(elapsed * 1000, 3),
            detail=type(exc).__name__,
        )
    elapsed = time.perf_counter() - started
    metrics.dependency_up.labels(name).set(1)
    metrics.dependency_check_duration_seconds.labels(name).set(elapsed)
    return DependencyHealth(
        name=name,
        status=DependencyStatus.UP,
        required=required,
        latency_ms=round(elapsed * 1000, 3),
    )


def summarise(dependencies: list[DependencyHealth]) -> ReadinessStatus:
    if any(d.required and d.status is DependencyStatus.DOWN for d in dependencies):
        return ReadinessStatus.UNAVAILABLE
    if any(d.status is DependencyStatus.DOWN for d in dependencies):
        return ReadinessStatus.DEGRADED
    return ReadinessStatus.OK


async def readiness(
    *,
    database: Database,
    cache: Cache | None,
    clock: Clock,
    metrics: Metrics,
    timeout_seconds: float,
) -> ReadinessReport:
    checks = [
        check_dependency(
            "postgres",
            database.ping,
            required=True,
            timeout_seconds=timeout_seconds,
            metrics=metrics,
        )
    ]
    if cache is not None:
        # Redis is a cache/pub-sub, never a system of record: optional.
        checks.append(
            check_dependency(
                "redis",
                cache.ping,
                required=False,
                timeout_seconds=timeout_seconds,
                metrics=metrics,
            )
        )
    dependencies = list(await asyncio.gather(*checks))
    return ReadinessReport(
        status=summarise(dependencies), checked_at=clock.now(), dependencies=dependencies
    )
