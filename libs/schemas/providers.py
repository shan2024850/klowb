"""Provider-boundary schemas: raw events as received, and provider health.

A ``RawEvent`` is one message exactly as it arrived, stamped with the injected
clock's receipt time. Normalisation into canonical observations happens later
(docs/architecture.md section 5), so a payload that fails to parse can still be
quarantined with its hash and receipt time.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Self

from pydantic import Field, model_validator

from libs.domain.enums import HealthState
from libs.schemas.hashing import payload_hash_from_text
from libs.schemas.types import CanonicalModel, ProviderId, Sha256Hex, UtcDatetime

MAX_RAW_PAYLOAD_CHARS = 1_000_000


def raw_payload_hash(payload: str) -> str:
    """Hash of a raw message.

    Valid JSON is hashed in canonical form (independent of key order and
    whitespace, see ``libs.schemas.hashing``). Anything else — malformed JSON,
    non-JSON frames — is hashed as its exact UTF-8 bytes, so it can still be
    identified and quarantined.
    """
    try:
        return payload_hash_from_text(payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RawEvent(CanonicalModel):
    provider: ProviderId
    received_timestamp: UtcDatetime
    # Order of receipt within one provider session; ties in time stay ordered.
    receive_sequence: int = Field(ge=0)
    payload: str = Field(max_length=MAX_RAW_PAYLOAD_CHARS)
    raw_payload_hash: Sha256Hex

    @model_validator(mode="after")
    def _check_hash(self) -> Self:
        if self.raw_payload_hash != raw_payload_hash(self.payload):
            raise ValueError("raw_payload_hash does not match payload")
        return self

    @classmethod
    def capture(
        cls, *, provider: str, payload: str, received_timestamp: datetime, receive_sequence: int
    ) -> RawEvent:
        return cls(
            provider=provider,
            payload=payload,
            received_timestamp=received_timestamp,
            receive_sequence=receive_sequence,
            raw_payload_hash=raw_payload_hash(payload),
        )


class ProviderHealthSnapshot(CanonicalModel):
    provider: ProviderId
    state: HealthState
    last_message_at: UtcDatetime | None = None
    messages_total: int = Field(default=0, ge=0)
    # Keys are provider error kinds (libs.providers.errors.ErrorKind values).
    errors_total: dict[str, int] = Field(default_factory=dict)
    reconnects_total: int = Field(default=0, ge=0)
    sequence_gaps_total: int = Field(default=0, ge=0)
    circuit_state: str | None = None
    detail: str | None = Field(default=None, max_length=500)
