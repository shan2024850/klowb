"""P1-UNIT-003: price/size validation and Decimal precision."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from tests import factories


@pytest.mark.parametrize("bad", ["0", "-1", "-0.00000001", "NaN", "Infinity", "-Infinity"])
def test_p1_unit_003_non_positive_or_non_finite_prices_are_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        factories.trade(last=Decimal(bad))
    with pytest.raises(ValidationError):
        factories.quote(bid=Decimal(bad))
    with pytest.raises(ValidationError):
        factories.bar(close=Decimal(bad))


@pytest.mark.parametrize("bad", ["-1", "NaN", "Infinity"])
def test_p1_unit_003_negative_or_non_finite_sizes_are_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        factories.trade(trade_size=Decimal(bad))
    with pytest.raises(ValidationError):
        factories.quote(bid_size=Decimal(bad))
    with pytest.raises(ValidationError):
        factories.bar(volume=Decimal(bad))


def test_p1_unit_003_zero_size_trade_is_rejected_but_zero_quote_size_is_allowed() -> None:
    with pytest.raises(ValidationError):
        factories.trade(trade_size=Decimal("0"))
    assert factories.quote(bid_size=Decimal("0")).bid_size == 0


@pytest.mark.parametrize("value", [0.1, 64571.1, 1e-8])
def test_p1_unit_003_binary_floats_are_rejected(value: float) -> None:
    with pytest.raises(ValidationError, match="float"):
        factories.trade(last=value)
    with pytest.raises(ValidationError, match="float"):
        factories.trade(trade_size=value)


def test_p1_unit_003_booleans_are_rejected() -> None:
    with pytest.raises(ValidationError):
        factories.trade(last=True)


def test_p1_unit_003_json_numbers_are_rejected_on_the_canonical_boundary() -> None:
    payload = json.loads(factories.trade().model_dump_json())
    payload["last"] = 64571.2  # a JSON number would arrive as a binary float
    with pytest.raises(ValidationError, match="float"):
        type(factories.trade()).model_validate(payload)


def test_p1_unit_003_crypto_precision_is_preserved() -> None:
    size = Decimal("0.00000001")  # one satoshi
    price = Decimal("64571.12345678")
    observation = factories.trade(last=price, trade_size=size)
    assert observation.last == price
    assert observation.trade_size == size
    dumped = json.loads(observation.model_dump_json())
    assert dumped["last"] == "64571.12345678"
    assert dumped["trade_size"] == "0.00000001"
    restored = type(observation).model_validate_json(observation.model_dump_json())
    assert restored.trade_size.as_tuple() == size.as_tuple()


def test_p1_unit_003_more_than_eight_decimals_are_preserved() -> None:
    tiny = Decimal("0.000000000000000001")  # 18 dp, e.g. wei-denominated assets
    assert factories.trade(trade_size=tiny).trade_size == tiny


def test_p1_unit_003_forex_pip_and_pipette_precision_is_preserved() -> None:
    eurusd = factories.quote(
        asset_class="FX",
        canonical_symbol="EUR/USD",
        provider_symbol="EUR/USD",
        bid=Decimal("1.08345"),
        ask=Decimal("1.08347"),
    )
    assert eurusd.spread == Decimal("0.00002")  # 0.2 pip, exact
    usdjpy = factories.quote(
        asset_class="FX",
        canonical_symbol="USD/JPY",
        provider_symbol="USD/JPY",
        currency="JPY",
        bid=Decimal("151.234"),
        ask=Decimal("151.237"),
    )
    assert usdjpy.spread == Decimal("0.003")
    assert json.loads(eurusd.model_dump_json())["bid"] == "1.08345"


def test_p1_unit_003_trailing_zeros_survive_round_trip() -> None:
    observation = factories.trade(last=Decimal("64571.10"))
    assert json.loads(observation.model_dump_json())["last"] == "64571.10"


def test_p1_unit_003_strings_and_ints_are_accepted() -> None:
    assert factories.trade(last="64571.2").last == Decimal("64571.2")
    assert factories.trade(last=64571).last == Decimal(64571)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("0.00000001", "0.00000001"),
        ("0.000000000000000001", "0.000000000000000001"),
        ("1E-8", "0.00000001"),
        ("1E+3", "1000"),
        ("64571.10", "64571.10"),
        ("100000000", "100000000"),
    ],
)
def test_p1_unit_003_json_decimals_never_use_exponent_notation(value: str, text: str) -> None:
    observation = factories.trade(trade_size=Decimal(value))
    dumped = json.loads(observation.model_dump_json())
    assert dumped["trade_size"] == text
    assert "E" not in dumped["trade_size"].upper()
    assert Decimal(dumped["trade_size"]) == Decimal(value)
    assert observation.model_dump(mode="json")["trade_size"] == text
    # Python-mode dump keeps real Decimals for in-process use.
    assert isinstance(observation.model_dump()["trade_size"], Decimal)
