"""Reusable field types for canonical schemas.

Numeric policy (docs/architecture.md section 4.3): prices and quantities are
``Decimal``. Binary floats are rejected at the boundary so a precision-losing
parse can never slip into canonical data unnoticed — adapters must parse provider
JSON with ``parse_float=Decimal``.

Time policy (section 4.4): only timezone-aware datetimes, normalised to UTC.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
)

from libs.domain.clock import ensure_utc


def _reject_float(value: Any) -> Any:
    # bool is a subclass of int and is never a valid price or size.
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid decimal")
    if isinstance(value, float):
        raise ValueError(
            "binary float is not accepted for decimal fields; pass Decimal, int or str "
            "(parse provider JSON with parse_float=Decimal)"
        )
    return value


def decimal_to_plain_string(value: Decimal) -> str:
    """Fixed-point text with every digit preserved and never an exponent.

    ``str(Decimal("0.00000001"))`` is ``"1E-8"``; clients and humans should see
    ``"0.00000001"``. Trailing zeros are kept (``"64571.10"`` stays as is).
    """
    return format(value, "f")


# In JSON, decimals travel as plain fixed-point strings (never numbers, never exponents).
_DecimalJson = PlainSerializer(decimal_to_plain_string, return_type=str, when_used="json")

# Finite is enforced by Pydantic's Decimal validation (NaN/Infinity -> finite_number).
DecimalValue = Annotated[Decimal, BeforeValidator(_reject_float), _DecimalJson]
PositiveDecimal = Annotated[Decimal, BeforeValidator(_reject_float), Field(gt=0), _DecimalJson]
NonNegativeDecimal = Annotated[Decimal, BeforeValidator(_reject_float), Field(ge=0), _DecimalJson]

# Timezone-aware input only (naive -> validation error), stored as UTC.
UtcDatetime = Annotated[datetime, AwareDatetime, AfterValidator(ensure_utc)]

ProviderId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{1,31}$")]
Venue = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9_.\-]{0,15}$")]
CurrencyCode = Annotated[str, Field(pattern=r"^[A-Z0-9]{2,10}$")]
EntitlementId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_.\-]{0,63}$")]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
# Provider symbols are opaque but must be printable, non-empty and bounded.
ProviderSymbol = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[\x21-\x7e]+$")]


class CanonicalModel(BaseModel):
    """Base for canonical, immutable value objects.

    * ``frozen``: observations are facts; they are never mutated after creation.
    * ``extra='forbid'``: unknown fields are a contract violation, not noise.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=False)
