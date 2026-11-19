"""Prometheus metrics.

Each application instance owns its registry (no process-global state), which
keeps tests isolated and makes the exported set explicit.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


class Metrics:
    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry if registry is not None else CollectorRegistry()

        self.http_requests_total = Counter(
            "http_requests_total",
            "HTTP requests handled, by method, route template and status code.",
            ["method", "route", "status"],
            registry=self.registry,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds, by method and route template.",
            ["method", "route"],
            buckets=_LATENCY_BUCKETS,
            registry=self.registry,
        )
        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "HTTP requests currently being handled.",
            registry=self.registry,
        )
        self.unhandled_exceptions_total = Counter(
            "unhandled_exceptions_total",
            "Requests that ended in an unhandled exception.",
            ["route"],
            registry=self.registry,
        )
        self.dependency_up = Gauge(
            "dependency_up",
            "1 if the dependency answered its last health check, else 0.",
            ["dependency"],
            registry=self.registry,
        )
        self.dependency_check_duration_seconds = Gauge(
            "dependency_check_duration_seconds",
            "Duration of the last health check of the dependency.",
            ["dependency"],
            registry=self.registry,
        )
        self.app_info = Gauge(
            "app_info",
            "Constant 1; labels describe the running build and trading mode.",
            ["version", "environment", "trading_mode"],
            registry=self.registry,
        )

    def render(self) -> tuple[bytes, str]:
        """Exposition payload and its content type."""
        return generate_latest(self.registry), CONTENT_TYPE_LATEST
