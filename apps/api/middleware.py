"""Pure-ASGI middleware: security headers, request metrics/access log, error boundary.

Pure ASGI (rather than ``BaseHTTPMiddleware``) keeps streaming and WebSocket
behaviour intact and avoids response buffering.

Order (outermost first), set in ``apps.api.main``:

    CorrelationId -> SecurityHeaders -> RequestMetrics -> ErrorBoundary -> app

so that even an unhandled error produces a response that carries the correlation
id and the security headers, and is counted and logged.
"""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from apps.api.errors import error_payload
from libs.observability.logging import get_logger
from libs.observability.metrics import Metrics

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

log = get_logger(__name__)

# The API serves JSON only, so the policy can be maximally strict.
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_BASE_HEADERS: tuple[tuple[bytes, bytes], ...] = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cross-origin-resource-policy", b"same-origin"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
    (b"cache-control", b"no-store"),
)
# Interactive API docs load assets from a CDN; they are disabled in production.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


def route_template(scope: Scope) -> str:
    """Low-cardinality label: the matched route's path template, not the raw URL."""
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "unmatched"


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_docs = scope.get("path", "").startswith(_DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {name.lower() for name, _ in message.get("headers", [])}
                headers = list(message.get("headers", []))
                for name, value in _BASE_HEADERS:
                    if name not in existing:
                        headers.append((name, value))
                if not is_docs and b"content-security-policy" not in existing:
                    headers.append((b"content-security-policy", _API_CSP.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RequestMetricsMiddleware:
    """Counts and times every HTTP request and writes one access-log line."""

    def __init__(self, app: ASGIApp, *, metrics: Metrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_holder = {"status": 500}
        started = time.perf_counter()
        self.metrics.http_requests_in_progress.inc()

        async def send_recording_status(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = int(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_recording_status)
        finally:
            duration = time.perf_counter() - started
            method = str(scope.get("method", "GET"))
            route = route_template(scope)
            status = status_holder["status"]
            self.metrics.http_requests_in_progress.dec()
            self.metrics.http_requests_total.labels(method, route, str(status)).inc()
            self.metrics.http_request_duration_seconds.labels(method, route).observe(duration)
            log.info(
                "http_request",
                method=method,
                path=scope.get("path"),
                route=route,
                status=status,
                duration_ms=round(duration * 1000, 3),
            )


class ErrorBoundaryMiddleware:
    """Turn an unhandled exception into the standard 500 envelope.

    Runs inside the header/correlation middleware so the 500 response still
    carries ``X-Request-ID`` and the security headers. Nothing about the
    exception is sent to the client.
    """

    def __init__(self, app: ASGIApp, *, metrics: Metrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_tracking(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_tracking)
        except Exception:
            self.metrics.unhandled_exceptions_total.labels(route_template(scope)).inc()
            log.exception("unhandled_exception", path=scope.get("path"))
            if response_started:
                # Headers are gone; the only honest option is to abort the stream.
                raise
            body = json.dumps(error_payload(500, "Internal server error")).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
