"""P2-UNIT-001: every MarketDataProvider passes the shared conformance suite."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from datetime import timedelta

import pytest

from libs.providers.clock import VirtualClock
from libs.providers.errors import ProviderError
from libs.providers.mock.provider import MockConfig, MockProvider
from libs.schemas.market import Observation
from libs.schemas.providers import RawEvent
from tests.contract.provider_conformance import ConformanceCase, assert_provider_conformance


async def test_p2_unit_001_mock_provider_conforms() -> None:
    def make(clock: VirtualClock) -> MockProvider:
        return MockProvider(clock, MockConfig(seed=7, interval_seconds=1.0))

    await assert_provider_conformance(
        ConformanceCase(
            make_provider=make,
            step=timedelta(seconds=1),
            malformed_payload='{"message": {"type": "trade", "symbol": "SECRET-MARKER"',
            leak_marker="SECRET-MARKER",
        )
    )


async def test_p2_unit_001_unknown_symbol_is_classified_without_leaking() -> None:
    def make(clock: VirtualClock) -> MockProvider:
        return MockProvider(clock, MockConfig(seed=7))

    await assert_provider_conformance(
        ConformanceCase(
            make_provider=make,
            step=timedelta(seconds=1),
            malformed_payload=(
                '{"message": {"type": "quote", "symbol": "SECRET-MARKER", "seq": 1,'
                ' "ts": "2026-11-18T14:30:00Z", "bid": "1", "ask": "2",'
                ' "bid_size": "1", "ask_size": "1"}}'
            ),
            leak_marker="SECRET-MARKER",
            events=5,
        )
    )


# The suite itself must reject broken adapters; otherwise it proves nothing.


class _WrongClockProvider(MockProvider):
    """Stamps receipt time from somewhere other than the injected clock."""

    async def stream(self) -> AsyncGenerator[RawEvent]:
        async for event in super().stream():
            yield event.model_copy(
                update={"received_timestamp": event.received_timestamp + timedelta(hours=1)}
            )


class _LeakyErrorProvider(MockProvider):
    """Puts raw payload text into its error detail."""

    def normalize(self, event: RawEvent) -> Sequence[Observation]:
        try:
            return super().normalize(event)
        except ProviderError as error:
            raise ProviderError(error.kind, detail=event.payload) from None


@pytest.mark.parametrize("broken", [_WrongClockProvider, _LeakyErrorProvider])
async def test_p2_unit_001_suite_rejects_non_conforming_providers(
    broken: type[MockProvider],
) -> None:
    with pytest.raises(AssertionError):
        await assert_provider_conformance(
            ConformanceCase(
                make_provider=lambda clock: broken(clock, MockConfig(seed=7)),
                step=timedelta(seconds=1),
                malformed_payload='{"message": {"type": "trade", "symbol": "SECRET-MARKER"',
                leak_marker="SECRET-MARKER",
                events=5,
            )
        )
