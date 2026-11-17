"""Structured JSON logging.

One pipeline for both structlog loggers and standard-library loggers (uvicorn,
SQLAlchemy, …): every line is a JSON object with ``timestamp`` (UTC), ``level``,
``logger``, ``event`` and any bound context such as ``correlation_id``.
Secrets are removed by :mod:`libs.observability.redaction`.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, TextIO

import structlog
from structlog.typing import Processor

from libs.observability.redaction import redact_processor


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        redact_processor,
    ]


def configure_logging(
    level: str = "INFO",
    *,
    json_output: bool = True,
    stream: TextIO | None = None,
    service: str = "klowb-api",
) -> None:
    """Configure logging for the whole process. Safe to call more than once."""
    shared = _shared_processors()

    def add_service(_: Any, __: str, event_dict: structlog.typing.EventDict) -> Any:
        event_dict.setdefault("service", service)
        return event_dict

    renderer: Processor = (
        structlog.processors.JSONRenderer(sort_keys=True)
        if json_output
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[*shared, add_service],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            # Redact again after formatting: exception text is rendered late.
            redact_processor,
            renderer,
        ],
    )
    handler = logging.StreamHandler(stream if stream is not None else sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Uvicorn installs its own handlers; route them through ours instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    # The access log is produced by our middleware with a correlation id.
    logging.getLogger("uvicorn.access").disabled = True

    structlog.configure(
        processors=[
            *shared,
            add_service,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(name)
    return logger
