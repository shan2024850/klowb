# 0006 — First streaming provider: Kraken WebSocket v2

- Status: Accepted
- Date: 2026-11-17

## Context

Phase 3 calls for "one real crypto streaming provider with reconnect and
data-quality handling". Candidates in the brief: Binance, Coinbase, Kraken, and
CCXT as an abstraction. Verified on 2026-11-17 from official docs and by live
probes from the development environment:

| | Kraken WS v2 | Coinbase Exchange feed | Binance global |
|---|---|---|---|
| Public market data without auth | yes | yes | yes |
| Reachable from the dev environment | yes (REST + WS) | yes (REST + WS) | **no — HTTP 451** |
| Sequence for gap detection | per-book `trade_id` on trades; CRC32 checksum on book | per-product `sequence` (+1 per message) | per-stream update ids |
| Heartbeat / liveness | automatic `heartbeat` when idle; `ping`→`pong`; `status` channel with engine state | `heartbeat` channel | ping/pong frames |
| Documented reconnect guidance | yes (≈150 attempts / 10 min per IP; ≥ 5 s after maintenance) | not on the page read | 300 connections / 5 min per IP |
| Number encoding | JSON numbers (decode as Decimal) | strings | strings |

## Decision

- Implement a **native Kraken WebSocket v2 adapter** (plus REST for backfill and
  instrument metadata) as the first real provider.
- Label its data `REALTIME_SINGLE_VENUE`, venue `KRAKEN`, entitlement
  `kraken-public`, `redistribution_allowed=false`.
- **Coinbase Exchange** is the documented second venue / fallback; its per-message
  sequence makes it a good cross-check.
- Do **not** start with CCXT: the first adapter must exercise our own contract —
  heartbeat, status, sequence gaps, reconnect budgets, Decimal parsing, provenance
  — and a unifying layer would hide exactly those details.
- Binance is not integrated in the development environment because it cannot be
  reached there; no attempt is made to work around the restriction.

## Alternatives considered

- **Coinbase first:** equally viable technically; Kraken's explicit `status`
  channel, documented reconnect limits and engine-state semantics tipped the
  choice.
- **CCXT first:** fastest breadth, least insight into feed integrity.

## Consequences

- Kraken sends prices as JSON numbers: payloads must be parsed with
  `parse_float=Decimal`.
- Live messages contain fields missing from the docs (`trades` on ticker,
  `upcoming_maintenance` on status): models must ignore unknown fields.
- Default tests use recorded fixtures and a local fake server; the live test is
  opt-in.

## Revisit when

Kraken changes its public API terms or reliability, or the operator's jurisdiction
makes another venue the natural primary.
