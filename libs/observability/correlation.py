"""Correlation IDs.

Each inbound request gets an ID (taken from ``X-Request-ID`` when it is well
formed, otherwise generated). The ID is bound to the logging context for the
duration of the request and echoed in the response header, so one request can be
traced across log lines, background work it starts and downstream calls.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog

HEADER_NAME = "x-request-id"
_VALID = re.compile(r"^[A-Za-z0-9._\-]{8,128}$")

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def accept_or_generate(candidate: str | None) -> str:
    """Use a client-supplied ID only if it is safe to log and echo."""
    if candidate is not None and _VALID.fullmatch(candidate):
        return candidate
    return new_correlation_id()


class CorrelationIdMiddleware:
    """Pure ASGI middleware (no response buffering; works for HTTP and WebSocket)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        incoming: str | None = None
        for name, value in scope.get("headers", []):
            if name == HEADER_NAME.encode():
                incoming = value.decode("latin-1")
                break
        correlation_id = accept_or_generate(incoming)
        scope.setdefault("state", {})["correlation_id"] = correlation_id

        token = _correlation_id.set(correlation_id)
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != HEADER_NAME.encode()
                ]
                headers.append((HEADER_NAME.encode(), correlation_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            structlog.contextvars.unbind_contextvars("correlation_id")
            _correlation_id.reset(token)
