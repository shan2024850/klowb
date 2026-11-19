"""The contract every market-data provider adapter implements.

Responsibilities are split so that nothing raises out of a stream loop:

* ``stream`` yields ``RawEvent`` messages exactly as received, timestamped with
  the injected clock;
* ``normalize`` turns one raw event into canonical observations, or raises a
  classified ``ProviderError`` (the normaliser in ``services.market_data``
  converts that into a quarantine record);
* ``health`` reports a snapshot at any time;
* ``aclose`` ends the stream cleanly and is idempotent.

Every implementation must pass ``tests/contract/provider_conformance.py``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from typing import Protocol, runtime_checkable

from libs.schemas.market import Observation
from libs.schemas.providers import ProviderHealthSnapshot, RawEvent


@runtime_checkable
class MarketDataProvider(Protocol):
    provider_id: str

    def stream(self) -> AsyncGenerator[RawEvent]:
        """Raw messages in receipt order until ``aclose`` is called."""
        ...

    def normalize(self, event: RawEvent) -> Sequence[Observation]:
        """Canonical observations for one raw event, or a classified ProviderError."""
        ...

    def health(self) -> ProviderHealthSnapshot: ...

    async def aclose(self) -> None: ...
