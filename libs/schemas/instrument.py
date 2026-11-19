"""Tradable instrument metadata (docs/architecture.md section 4.1).

Derivative fields exist from the start (and stay ``None`` for spot) so futures and
options can be added without redesigning the core.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Self

from pydantic import Field, model_validator

from libs.domain.enums import AssetClass, InstrumentKind, InstrumentStatus, OptionRight
from libs.domain.symbols import make_instrument_id, split_pair, validate_canonical_symbol
from libs.schemas.types import CanonicalModel, CurrencyCode, PositiveDecimal

CalendarId = Annotated[str, Field(pattern=r"^[A-Z0-9_]{2,32}$")]

_PAIR_CLASSES = frozenset({AssetClass.CRYPTO, AssetClass.FX})
_DERIVATIVE_KINDS = frozenset(
    {InstrumentKind.FUTURE, InstrumentKind.OPTION, InstrumentKind.PERPETUAL}
)


class Instrument(CanonicalModel):
    asset_class: AssetClass
    canonical_symbol: str
    kind: InstrumentKind = InstrumentKind.SPOT
    name: str | None = Field(default=None, max_length=200)
    # Quote currency of prices (for pairs this equals the quote asset).
    currency: CurrencyCode
    base: CurrencyCode | None = None
    quote: CurrencyCode | None = None
    price_increment: PositiveDecimal
    quantity_increment: PositiveDecimal
    min_notional: PositiveDecimal | None = None
    calendar_id: CalendarId
    status: InstrumentStatus = InstrumentStatus.ACTIVE

    # Derivative-ready fields (None for spot).
    underlying_id: str | None = None
    expiry: date | None = None
    strike: PositiveDecimal | None = None
    option_right: OptionRight | None = None
    multiplier: PositiveDecimal | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        validate_canonical_symbol(self.asset_class, self.canonical_symbol)

        if self.asset_class in _PAIR_CLASSES:
            base, quote = split_pair(self.canonical_symbol)
            if self.base is not None and self.base != base:
                raise ValueError("base does not match canonical_symbol")
            if self.quote is not None and self.quote != quote:
                raise ValueError("quote does not match canonical_symbol")
            if self.currency != quote:
                raise ValueError("currency must equal the quote asset for a BASE/QUOTE pair")

        if self.kind is InstrumentKind.SPOT:
            for field_name in ("underlying_id", "expiry", "strike", "option_right", "multiplier"):
                if getattr(self, field_name) is not None:
                    raise ValueError(f"{field_name} must be None for a spot instrument")
        if self.kind is InstrumentKind.OPTION and None in (
            self.underlying_id,
            self.expiry,
            self.strike,
            self.option_right,
        ):
            raise ValueError("an option needs underlying_id, expiry, strike and option_right")
        if self.kind is InstrumentKind.FUTURE and (
            self.underlying_id is None or self.expiry is None
        ):
            raise ValueError("a future needs underlying_id and expiry")
        if self.kind is not InstrumentKind.OPTION and (
            self.strike is not None or self.option_right is not None
        ):
            raise ValueError("strike/option_right are only valid for options")
        if self.kind in _DERIVATIVE_KINDS - {InstrumentKind.PERPETUAL} and self.multiplier is None:
            raise ValueError("futures and options need a contract multiplier")
        return self

    @property
    def instrument_id(self) -> str:
        return make_instrument_id(self.asset_class, self.canonical_symbol)

    @property
    def is_tradable(self) -> bool:
        return self.status is InstrumentStatus.ACTIVE
