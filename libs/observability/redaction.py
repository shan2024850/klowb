"""Keep secrets out of logs.

Three layers, applied to every log event:

1. keys whose name looks sensitive are masked;
2. secret-wrapper objects (anything exposing ``get_secret_value``) are masked;
3. credentials embedded in URLs inside strings are masked.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping
from typing import Any

REDACTED = "[REDACTED]"

_SENSITIVE_KEY = re.compile(
    r"(secret|password|passwd|token|api[_-]?key|apikey|authorization|cookie|credential|"
    r"private[_-]?key|session[_-]?id|dsn|database[_-]?url|redis[_-]?url)",
    re.IGNORECASE,
)
# scheme://user:password@host  ->  scheme://user:[REDACTED]@host
_URL_CREDENTIALS = re.compile(
    r"(?P<prefix>[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@]*:)[^\s@/]+(?P<suffix>@)"
)
# Bearer/Basic tokens inside free text.
_AUTH_HEADER = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=\-]{8,}")

_MAX_DEPTH = 6


def is_sensitive_key(key: str) -> bool:
    return bool(_SENSITIVE_KEY.search(key))


def redact_text(text: str) -> str:
    text = _URL_CREDENTIALS.sub(rf"\g<prefix>{REDACTED}\g<suffix>", text)
    return _AUTH_HEADER.sub(lambda match: f"{match.group(1)} {REDACTED}", text)


def redact_value(value: Any, *, _depth: int = 0) -> Any:
    if hasattr(value, "get_secret_value"):
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if _depth >= _MAX_DEPTH:
        # Never hand an uninspected subtree to the JSON renderer.
        return REDACTED
    if isinstance(value, Mapping):
        return {
            key: REDACTED
            if isinstance(key, str) and is_sensitive_key(key)
            else redact_value(item, _depth=_depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    if isinstance(value, BaseException):
        return redact_text(repr(value))
    return value


def redact_processor(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """structlog processor applying the three redaction layers."""
    for key in list(event_dict):
        if key == "event":
            if isinstance(event_dict[key], str):
                event_dict[key] = redact_text(event_dict[key])
            continue
        if is_sensitive_key(key):
            event_dict[key] = REDACTED
        else:
            event_dict[key] = redact_value(event_dict[key])
    return event_dict
