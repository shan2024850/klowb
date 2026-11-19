"""P1-UNIT-001: canonical observations carry the brief's provenance fields."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from libs.domain.enums import DataType, FeedQuality
from libs.schemas.market import (
    PROVENANCE_FIELDS,
    BarObservation,
    Observation,
    ObservationAdapter,
    QuoteObservation,
    TickerObservation,
    TradeObservation,
)
from tests import factories

BRIEF_PROVENANCE = {
    "provider",
    "asset_class",
    "venue",
    "canonical_symbol",
    "provider_symbol",
    "event_timestamp",
    "received_timestamp",
    "data_type",
    "feed_quality",
    "delay_seconds",
    "currency",
    "sequence_number",
    "is_adjusted",
    "entitlement",
    "redistribution_allowed",
    "raw_payload_hash",
}
BRIEF_VALUE_FIELDS = {"bid", "ask", "last", "open", "high", "low", "close", "volume", "trade_size"}
VARIANTS = (TradeObservation, QuoteObservation, BarObservation, TickerObservation)


def test_p1_unit_001_every_variant_has_every_provenance_field() -> None:
    assert PROVENANCE_FIELDS == BRIEF_PROVENANCE
    for variant in VARIANTS:
        missing = BRIEF_PROVENANCE - set(variant.model_fields)
        assert not missing, f"{variant.__name__} lacks {missing}"


def test_p1_unit_001_value_fields_from_the_brief_exist_on_some_variant() -> None:
    available = set().union(*(set(v.model_fields) for v in VARIANTS))
    assert available >= BRIEF_VALUE_FIELDS


def test_p1_unit_001_feed_quality_has_exactly_the_required_values() -> None:
    assert {q.value for q in FeedQuality} == {
        "REALTIME_CONSOLIDATED",
        "REALTIME_SINGLE_VENUE",
        "REALTIME_EXCHANGE",
        "DELAYED",
        "EOD",
        "UNOFFICIAL",
        "SIMULATED",
    }


def test_p1_unit_001_data_type_discriminates_the_union() -> None:
    assert {d.value for d in DataType} == {"TRADE", "QUOTE", "BAR", "TICKER"}
    samples: dict[DataType, Observation] = {
        DataType.TRADE: factories.trade(),
        DataType.QUOTE: factories.quote(),
        DataType.BAR: factories.bar(),
        DataType.TICKER: factories.ticker(),
    }
    for data_type, sample in samples.items():
        assert sample.data_type is data_type
        parsed = ObservationAdapter.validate_json(sample.model_dump_json())
        assert type(parsed) is type(sample)
        assert parsed == sample


def test_p1_unit_001_unknown_data_type_is_rejected() -> None:
    payload = factories.trade().model_dump(mode="json")
    payload["data_type"] = "ORDERBOOK"
    with pytest.raises(ValidationError):
        ObservationAdapter.validate_python(payload)


def test_p1_unit_001_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        factories.trade(surprise="x")


def test_p1_unit_001_observations_are_immutable() -> None:
    observation = factories.trade()
    with pytest.raises(ValidationError):
        observation.last = observation.last + 1  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", "Kraken"),  # must be a lower-case id
        ("provider", ""),
        ("venue", "kraken"),  # must be upper case
        ("currency", "usd"),
        ("entitlement", "Has Spaces"),
        ("raw_payload_hash", "abc"),
        ("raw_payload_hash", "Z" * 64),
        ("provider_symbol", ""),
        ("provider_symbol", "BTC USD"),
        ("sequence_number", -1),
        ("delay_seconds", -1),
    ],
)
def test_p1_unit_001_malformed_provenance_is_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        factories.trade(**{field: value})


@pytest.mark.parametrize(
    ("asset_class", "symbol"),
    [
        ("CRYPTO", "BTCUSD"),  # pair separator required
        ("CRYPTO", "btc/usd"),
        ("CRYPTO", "BTC/BTC"),
        ("FX", "EUR/USDT"),  # FX codes are three letters
        ("EQUITY", "aapl"),
        ("EQUITY", "AAPL/USD"),
        ("EQUITY", "1234"),  # needs at least one letter
        ("EQUITY", ""),
    ],
)
def test_p1_unit_001_malformed_symbols_are_rejected(asset_class: str, symbol: str) -> None:
    with pytest.raises(ValidationError):
        factories.trade(asset_class=asset_class, canonical_symbol=symbol)


def test_p1_unit_001_instrument_id_is_derived_from_class_and_symbol() -> None:
    assert factories.trade().instrument_id == "crypto:BTC/USD"
    equity = factories.trade(
        asset_class="EQUITY", canonical_symbol="BRK.B", provider_symbol="BRK.B"
    )
    assert equity.instrument_id == "equity:BRK.B"
