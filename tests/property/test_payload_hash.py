"""P1-PROP-002: raw_payload_hash is deterministic and independent of key order/whitespace."""

from __future__ import annotations

import json
import random
from decimal import Decimal
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from libs.schemas.hashing import (
    canonical_json,
    parse_json_exact,
    payload_hash,
    payload_hash_from_text,
)

scalars = (
    st.none()
    | st.booleans()
    | st.integers(min_value=-(10**18), max_value=10**18)
    | st.decimals(
        allow_nan=False, allow_infinity=False, places=8, min_value=-(10**9), max_value=10**9
    )
    | st.text(max_size=20)
)
json_values = st.recursive(
    scalars,
    lambda children: (
        st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=8), children, max_size=5)
    ),
    max_leaves=25,
)


def shuffle_keys(value: Any, rng: random.Random) -> Any:
    if isinstance(value, dict):
        items = [(key, shuffle_keys(item, rng)) for key, item in value.items()]
        rng.shuffle(items)
        return dict(items)
    if isinstance(value, list):
        return [shuffle_keys(item, rng) for item in value]
    return value


def to_text(value: Any, *, indent: int | None, separators: tuple[str, str] | None) -> str:
    """Serialise with Decimals as JSON numbers using a given whitespace style."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        pad = "" if indent is None else "\n" + " " * indent
        item_sep, key_sep = separators or (", ", ": ")
        inner = (item_sep + pad).join(
            json.dumps(key) + key_sep + to_text(item, indent=indent, separators=separators)
            for key, item in value.items()
        )
        return "{" + pad + inner + pad + "}"
    if isinstance(value, list):
        item_sep = (separators or (", ", ": "))[0]
        return (
            "["
            + item_sep.join(to_text(i, indent=indent, separators=separators) for i in value)
            + "]"
        )
    return json.dumps(value)


@given(value=json_values, seed=st.integers(0, 2**32 - 1))
@settings(max_examples=300, deadline=None)
def test_p1_prop_002_hash_ignores_key_order_and_whitespace(value: Any, seed: int) -> None:
    compact = to_text(value, indent=None, separators=(",", ":"))
    rng = random.Random(seed)  # noqa: S311 - deterministic shuffle, not cryptography
    spaced = to_text(shuffle_keys(value, rng), indent=2, separators=(" , ", " : "))

    first = payload_hash_from_text(compact)
    assert first == payload_hash_from_text(compact), "hash must be deterministic"
    assert first == payload_hash_from_text(spaced), "hash must ignore key order and whitespace"
    assert first == payload_hash(parse_json_exact(compact))
    assert len(first) == 64
    assert set(first) <= set("0123456789abcdef")


@given(value=json_values)
@settings(max_examples=200, deadline=None)
def test_p1_prop_002_canonical_form_round_trips(value: Any) -> None:
    canonical = canonical_json(value)
    assert canonical_json(parse_json_exact(canonical)) == canonical


def test_p1_prop_002_different_payloads_hash_differently() -> None:
    a = payload_hash_from_text('{"price": 64571.1, "qty": 0.5}')
    b = payload_hash_from_text('{"price": 64571.2, "qty": 0.5}')
    c = payload_hash_from_text('{"price": "64571.1", "qty": 0.5}')  # string vs number
    d = payload_hash_from_text('{"price": 64571.10, "qty": 0.5}')  # different exact text
    assert len({a, b, c, d}) == 4


def test_p1_prop_002_known_vector() -> None:
    text = '{ "b": [1, 2.50, "x"], "a": null, "c": {"z": true, "y": false} }'
    assert (
        canonical_json(parse_json_exact(text))
        == '{"a":null,"b":[1,2.50,"x"],"c":{"y":false,"z":true}}'
    )
    assert payload_hash_from_text(text) == payload_hash_from_text(
        '{"c":{"y":false,"z":true},"a":null,"b":[1,2.50,"x"]}'
    )


def test_p1_prop_002_binary_floats_and_non_finite_numbers_are_refused() -> None:
    with pytest.raises(TypeError, match="float"):
        payload_hash({"price": 64571.1})
    with pytest.raises(ValueError, match="non-finite"):
        payload_hash({"price": Decimal("NaN")})
    with pytest.raises(TypeError, match="unsupported"):
        payload_hash({"when": object()})
    with pytest.raises(TypeError, match="keys"):
        payload_hash({1: "x"})
