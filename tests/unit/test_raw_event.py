"""RawEvent hashing (supports P2-UNIT-001 provenance and later quarantine of bad payloads)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from libs.schemas.hashing import payload_hash_from_text
from libs.schemas.providers import RawEvent, raw_payload_hash

T0 = datetime(2026, 11, 18, tzinfo=UTC)


def test_json_payloads_hash_canonically() -> None:
    a = RawEvent.capture(
        provider="mock", payload='{"b":1, "a":2}', received_timestamp=T0, receive_sequence=0
    )
    b = RawEvent.capture(
        provider="mock", payload='{ "a": 2, "b": 1 }', received_timestamp=T0, receive_sequence=1
    )
    assert a.raw_payload_hash == b.raw_payload_hash == payload_hash_from_text('{"a":2,"b":1}')


def test_malformed_payloads_still_get_a_hash() -> None:
    event = RawEvent.capture(
        provider="mock", payload='{"a":', received_timestamp=T0, receive_sequence=0
    )
    assert event.raw_payload_hash == raw_payload_hash('{"a":')
    assert len(event.raw_payload_hash) == 64


def test_hash_must_match_payload() -> None:
    with pytest.raises(ValidationError, match="does not match"):
        RawEvent(
            provider="mock",
            payload="{}",
            received_timestamp=T0,
            receive_sequence=0,
            raw_payload_hash="0" * 64,
        )
