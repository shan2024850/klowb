"""Deterministic hashing of raw provider payloads (``raw_payload_hash``).

The hash identifies the exact message fragment an observation was derived from,
giving idempotency and auditability without storing every payload.

Canonical form: UTF-8 JSON with object keys sorted, no insignificant whitespace,
and numbers written in fixed-point notation with all their digits (trailing zeros
kept, no exponent). Therefore the hash does not depend on key order or whitespace
of the original message.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialise a parsed JSON value canonically.

    Accepts dict / list / tuple / str / int / Decimal / bool / None. Binary floats
    are refused: provider payloads must be parsed with ``parse_float=Decimal`` so
    numbers keep their exact text.
    """
    return "".join(_encode(value))


def _encode(value: Any) -> list[str]:
    if value is None:
        return ["null"]
    if value is True:
        return ["true"]
    if value is False:
        return ["false"]
    if isinstance(value, str):
        return [json.dumps(value, ensure_ascii=False)]
    if isinstance(value, int):
        return [str(value)]
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("non-finite number cannot be hashed canonically")
        # Fixed-point text: stable, exponent-free, keeps trailing zeros.
        return [format(value, "f")]
    if isinstance(value, float):
        raise TypeError("binary float in payload; parse JSON with parse_float=Decimal")
    if isinstance(value, dict):
        parts = ["{"]
        for index, key in enumerate(sorted(value)):
            if not isinstance(key, str):
                raise TypeError("JSON object keys must be strings")
            if index:
                parts.append(",")
            parts.append(json.dumps(key, ensure_ascii=False))
            parts.append(":")
            parts.extend(_encode(value[key]))
        parts.append("}")
        return parts
    if isinstance(value, (list, tuple)):
        parts = ["["]
        for index, item in enumerate(value):
            if index:
                parts.append(",")
            parts.extend(_encode(item))
        parts.append("]")
        return parts
    raise TypeError(f"unsupported type in payload: {type(value).__name__}")


def parse_json_exact(text: str | bytes) -> Any:
    """Parse JSON keeping decimal numbers exact (no binary float)."""
    return json.loads(text, parse_float=Decimal)


def payload_hash(value: Any) -> str:
    """SHA-256 hex digest of the canonical form of a parsed JSON value."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def payload_hash_from_text(text: str | bytes) -> str:
    """Hash raw JSON text; equal for any key order / whitespace of the same data."""
    return payload_hash(parse_json_exact(text))
