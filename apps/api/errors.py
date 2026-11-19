"""Uniform error envelope.

Every error response has the shape::

    {"error": {"code": "...", "message": "...", "correlation_id": "...", "details": ...}}

Internal details (stack traces, SQL, connection strings) are never returned.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from libs.observability.correlation import get_correlation_id
from libs.schemas.system import ErrorBody, ErrorEnvelope

_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_error",
    503: "unavailable",
}


def error_code_for(status_code: int) -> str:
    return _CODES.get(status_code, "error")


def error_payload(
    status_code: int, message: str | None = None, *, code: str | None = None, details: Any = None
) -> dict[str, Any]:
    body = ErrorBody(
        code=code or error_code_for(status_code),
        message=message or HTTPStatus(status_code).phrase,
        correlation_id=get_correlation_id(),
        details=details,
    )
    return ErrorEnvelope(error=body).model_dump(mode="json")


def error_response(
    status_code: int,
    message: str | None = None,
    *,
    code: str | None = None,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_payload(status_code, message, code=code, details=details),
        headers=headers,
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    # Return where and why, never the offending input (it may contain secrets).
    return [
        {
            "location": [str(part) for part in error.get("loc", ())],
            "message": str(error.get("msg", "")),
            "type": str(error.get("type", "")),
        }
        for error in exc.errors()
    ]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else None
        details = None if isinstance(exc.detail, str) else exc.detail
        headers = dict(exc.headers) if exc.headers else None
        return error_response(exc.status_code, message, details=details, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(422, "Request validation failed", details=_validation_details(exc))
