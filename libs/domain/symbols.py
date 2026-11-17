"""Canonical symbol rules (docs/architecture.md section 4.1)."""

from __future__ import annotations

import re

from libs.domain.enums import AssetClass

# Equities/ETFs: upper-case ticker, optional class/series suffix (BRK.B, BF-B).
_EQUITY = re.compile(r"^(?=[A-Z0-9]*[A-Z])[A-Z0-9]{1,10}([.\-][A-Z0-9]{1,4})?$")
# Crypto: BASE/QUOTE asset codes.
_CRYPTO_PAIR = re.compile(r"^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$")
# FX: ISO-4217 style three-letter codes.
_FX_PAIR = re.compile(r"^[A-Z]{3}/[A-Z]{3}$")
# Derivatives are reserved; accept a conservative printable form.
_DERIVATIVE = re.compile(r"^[A-Z0-9][A-Z0-9 ._/\-]{0,31}$")

_PATTERNS: dict[AssetClass, re.Pattern[str]] = {
    AssetClass.EQUITY: _EQUITY,
    AssetClass.ETF: _EQUITY,
    AssetClass.CRYPTO: _CRYPTO_PAIR,
    AssetClass.FX: _FX_PAIR,
    AssetClass.FUTURE: _DERIVATIVE,
    AssetClass.OPTION: _DERIVATIVE,
}

_PAIR_CLASSES = frozenset({AssetClass.CRYPTO, AssetClass.FX})


def is_valid_canonical_symbol(asset_class: AssetClass, symbol: str) -> bool:
    return bool(_PATTERNS[asset_class].fullmatch(symbol))


def validate_canonical_symbol(asset_class: AssetClass, symbol: str) -> str:
    if not is_valid_canonical_symbol(asset_class, symbol):
        raise ValueError(
            f"malformed canonical symbol {symbol!r} for asset class {asset_class.value}"
        )
    if asset_class in _PAIR_CLASSES:
        base, quote = symbol.split("/")
        if base == quote:
            raise ValueError(f"base and quote must differ in {symbol!r}")
    return symbol


def split_pair(symbol: str) -> tuple[str, str]:
    """Split a ``BASE/QUOTE`` symbol."""
    base, sep, quote = symbol.partition("/")
    if not sep or not base or not quote:
        raise ValueError(f"{symbol!r} is not a BASE/QUOTE pair")
    return base, quote


def make_instrument_id(asset_class: AssetClass, canonical_symbol: str) -> str:
    """Stable identifier, e.g. ``crypto:BTC/USD`` or ``equity:AAPL``."""
    validate_canonical_symbol(asset_class, canonical_symbol)
    return f"{asset_class.value.lower()}:{canonical_symbol}"


def parse_instrument_id(instrument_id: str) -> tuple[AssetClass, str]:
    prefix, sep, symbol = instrument_id.partition(":")
    if not sep:
        raise ValueError(f"malformed instrument id {instrument_id!r}")
    try:
        asset_class = AssetClass(prefix.upper())
    except ValueError as exc:
        raise ValueError(f"unknown asset class in instrument id {instrument_id!r}") from exc
    if prefix != prefix.lower():
        raise ValueError(f"instrument id prefix must be lower case: {instrument_id!r}")
    validate_canonical_symbol(asset_class, symbol)
    return asset_class, symbol
