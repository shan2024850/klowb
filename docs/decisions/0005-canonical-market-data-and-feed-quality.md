# 0005 — Canonical market data model and feed quality

- Status: Accepted
- Date: 2026-11-17

## Context

The brief requires provider adapters behind canonical interfaces, a fixed list of
provenance fields on every observation, a `feed_quality` enum with seven minimum
values, visible feed quality in the UI, and a quality service that quarantines bad
data. Providers differ widely (Kraken sends JSON floats and a per-book trade id;
Coinbase sends strings and a per-product sequence; equity feeds may be single
venue or consolidated).

## Decision

- One canonical **`Observation`** family (discriminated union on `data_type`:
  `TRADE`, `QUOTE`, `BAR`, `TICKER`) sharing a provenance block with exactly the
  brief's fields (`docs/architecture.md` §4.2).
- **`Decimal`** for all prices and sizes in canonical models; conversion to float
  happens once at the feature-engine boundary.
- **Timezone-aware UTC** timestamps only; naive values are validation errors.
- **`feed_quality` semantics** are defined in `docs/data-providers.md` §1. It is
  assigned by the adapter from documented entitlement, is never upgraded
  downstream, and aggregates inherit the weakest input quality. Unverified
  provenance gets the weakest plausible label.
- **`redistribution_allowed` defaults to `false`** for every provider.
- **`raw_payload_hash`** = SHA-256 of the canonical JSON of the raw message
  fragment, giving idempotency and auditability without storing every payload.
- Pipeline: raw event → normaliser → quality service (`ACCEPT`, `ACCEPT_FLAGGED`,
  `QUARANTINE`) → bus. Schema violations and quality failures are **quarantined
  and surfaced**, never silently corrected or dropped.
- Instruments have a stable `instrument_id` (`asset_class:symbol`) and carry
  derivative-ready optional fields so futures/options do not require a redesign.

## Alternatives considered

- **One wide model with every field optional:** simpler to write, but allows
  nonsensical combinations and pushes validation into every consumer.
- **Floats everywhere:** faster, but loses crypto and FX precision and makes
  order quantities unsafe.
- **Trusting provider "real-time" labels:** rejected; the brief forbids presenting
  single-venue or delayed data as consolidated real-time.

## Consequences

- Each adapter needs explicit mapping code and contract fixtures.
- A crossed quote is representable; legitimacy is a quality-service decision.

## Revisit when

A new asset class cannot be expressed (e.g. option chains needing a different
observation shape) — extend the union, do not overload existing variants.
