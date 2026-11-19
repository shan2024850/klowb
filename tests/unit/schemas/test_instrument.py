"""P1-UNIT-006: instrument model and canonical symbol rules."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from libs.domain.enums import AssetClass, InstrumentKind, InstrumentStatus
from libs.domain.symbols import (
    is_valid_canonical_symbol,
    make_instrument_id,
    parse_instrument_id,
    split_pair,
)
from libs.schemas.instrument import Instrument


def crypto(**overrides: Any) -> Instrument:
    fields: dict[str, Any] = {
        "asset_class": AssetClass.CRYPTO,
        "canonical_symbol": "BTC/USD",
        "currency": "USD",
        "price_increment": Decimal("0.1"),
        "quantity_increment": Decimal("0.00000001"),
        "calendar_id": "CRYPTO_24_7",
    }
    fields.update(overrides)
    return Instrument(**fields)


def equity(**overrides: Any) -> Instrument:
    fields: dict[str, Any] = {
        "asset_class": AssetClass.EQUITY,
        "canonical_symbol": "AAPL",
        "currency": "USD",
        "price_increment": Decimal("0.01"),
        "quantity_increment": Decimal("1"),
        "calendar_id": "XNYS",
    }
    fields.update(overrides)
    return Instrument(**fields)


@pytest.mark.parametrize(
    ("asset_class", "symbol"),
    [
        (AssetClass.EQUITY, "AAPL"),
        (AssetClass.EQUITY, "BRK.B"),
        (AssetClass.EQUITY, "BF-B"),
        (AssetClass.EQUITY, "A"),
        (AssetClass.ETF, "SPY"),
        (AssetClass.CRYPTO, "BTC/USD"),
        (AssetClass.CRYPTO, "1INCH/USDT"),
        (AssetClass.FX, "EUR/USD"),
        (AssetClass.FX, "USD/JPY"),
    ],
)
def test_p1_unit_006_valid_canonical_symbols(asset_class: AssetClass, symbol: str) -> None:
    assert is_valid_canonical_symbol(asset_class, symbol)


@pytest.mark.parametrize(
    ("asset_class", "symbol"),
    [
        (AssetClass.EQUITY, "aapl"),
        (AssetClass.EQUITY, "AAPL "),
        (AssetClass.EQUITY, "AAPL/USD"),
        (AssetClass.EQUITY, "TOOLONGTICKER"),
        (AssetClass.EQUITY, "123"),
        (AssetClass.CRYPTO, "BTCUSD"),
        (AssetClass.CRYPTO, "BTC-USD"),
        (AssetClass.CRYPTO, "BTC/"),
        (AssetClass.CRYPTO, "/USD"),
        (AssetClass.FX, "EURUSD"),
        (AssetClass.FX, "EUR/US"),
        (AssetClass.FX, "eur/usd"),
    ],
)
def test_p1_unit_006_malformed_canonical_symbols(asset_class: AssetClass, symbol: str) -> None:
    assert not is_valid_canonical_symbol(asset_class, symbol)


def test_p1_unit_006_instrument_id_format_round_trips() -> None:
    assert make_instrument_id(AssetClass.CRYPTO, "BTC/USD") == "crypto:BTC/USD"
    assert make_instrument_id(AssetClass.EQUITY, "AAPL") == "equity:AAPL"
    assert make_instrument_id(AssetClass.FX, "EUR/USD") == "fx:EUR/USD"
    assert parse_instrument_id("crypto:BTC/USD") == (AssetClass.CRYPTO, "BTC/USD")
    assert parse_instrument_id("etf:SPY") == (AssetClass.ETF, "SPY")
    for bad in ("BTC/USD", "crypto:", "CRYPTO:BTC/USD", "bond:XYZ", "crypto:btc/usd"):
        with pytest.raises(ValueError, match=r"instrument id|symbol"):
            parse_instrument_id(bad)
    assert crypto().instrument_id == "crypto:BTC/USD"
    assert split_pair("BTC/USD") == ("BTC", "USD")


def test_p1_unit_006_derivative_fields_default_to_none_for_spot() -> None:
    for instrument in (crypto(), equity()):
        assert instrument.kind is InstrumentKind.SPOT
        assert instrument.underlying_id is None
        assert instrument.expiry is None
        assert instrument.strike is None
        assert instrument.option_right is None
        assert instrument.multiplier is None


def test_p1_unit_006_spot_rejects_derivative_fields() -> None:
    with pytest.raises(ValidationError, match="spot"):
        equity(strike=Decimal("100"))
    with pytest.raises(ValidationError, match="spot"):
        equity(expiry=date(2027, 1, 15))


def test_p1_unit_006_derivatives_are_expressible_without_schema_changes() -> None:
    option = Instrument(
        asset_class=AssetClass.OPTION,
        canonical_symbol="AAPL 270115C00200000",
        kind=InstrumentKind.OPTION,
        currency="USD",
        price_increment=Decimal("0.01"),
        quantity_increment=Decimal("1"),
        calendar_id="XNYS",
        underlying_id="equity:AAPL",
        expiry=date(2027, 1, 15),
        strike=Decimal("200"),
        option_right="CALL",
        multiplier=Decimal("100"),
    )
    assert option.instrument_id == "option:AAPL 270115C00200000"
    future = Instrument(
        asset_class=AssetClass.FUTURE,
        canonical_symbol="ESH7",
        kind=InstrumentKind.FUTURE,
        currency="USD",
        price_increment=Decimal("0.25"),
        quantity_increment=Decimal("1"),
        calendar_id="CME_GLOBEX",
        underlying_id="index:SPX",
        expiry=date(2027, 3, 19),
        multiplier=Decimal("50"),
    )
    assert future.multiplier == Decimal("50")
    with pytest.raises(ValidationError, match="option needs"):
        Instrument(
            asset_class=AssetClass.OPTION,
            canonical_symbol="AAPL 270115C00200000",
            kind=InstrumentKind.OPTION,
            currency="USD",
            price_increment=Decimal("0.01"),
            quantity_increment=Decimal("1"),
            calendar_id="XNYS",
            multiplier=Decimal("100"),
        )


@pytest.mark.parametrize("field", ["price_increment", "quantity_increment", "min_notional"])
@pytest.mark.parametrize("bad", ["0", "-0.01"])
def test_p1_unit_006_increments_must_be_positive(field: str, bad: str) -> None:
    with pytest.raises(ValidationError):
        crypto(**{field: Decimal(bad)})


def test_p1_unit_006_pair_metadata_must_match_the_symbol() -> None:
    assert crypto(base="BTC", quote="USD").base == "BTC"
    with pytest.raises(ValidationError, match="base"):
        crypto(base="ETH")
    with pytest.raises(ValidationError, match="quote"):
        crypto(quote="EUR")
    with pytest.raises(ValidationError, match="currency"):
        crypto(currency="EUR")


def test_p1_unit_006_status_controls_tradability() -> None:
    assert crypto().is_tradable is True
    assert crypto(status=InstrumentStatus.HALTED).is_tradable is False
    assert crypto(status=InstrumentStatus.DELISTED).is_tradable is False


def test_p1_unit_006_malformed_symbol_or_calendar_is_rejected() -> None:
    with pytest.raises(ValidationError, match="malformed"):
        crypto(canonical_symbol="BTCUSD")
    with pytest.raises(ValidationError):
        crypto(calendar_id="crypto 24/7")
