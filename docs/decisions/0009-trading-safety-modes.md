# 0009 — Trading safety modes and the live gate

- Status: Accepted
- Date: 2026-11-17

## Context

Brief: `TRADING_MODE=research` by default; modes `research`, `paper`, `live`;
live requires explicit environment configuration, broker credentials, a live
capability flag, human acknowledgement and risk configuration validation; never
silently fall back from paper to live; if live is not configured the application
continues normally in research/paper mode. The working instructions also forbid
enabling live trading or placing a real order.

## Decision

- `TRADING_MODE` ∈ {`research`, `paper`, `live`}, default `research`.
  - `research`: the order API rejects every order (`MODE_FORBIDS`).
  - `paper`: only simulated brokers; the Alpaca paper adapter is hard-wired to the
    paper base URL and refuses any other.
  - `live`: requires **all** gates — `TRADING_MODE=live`,
    `LIVE_TRADING_ENABLED=true`, live credentials, exact `LIVE_TRADING_ACK`
    phrase, validated and reviewed `RiskConfig`, and a per-session human arm
    action in the UI.
- If `TRADING_MODE=live` and any configuration gate is missing, **startup fails**
  with an explicit error. The system never substitutes another mode on its own.
- If `TRADING_MODE` is `research` or `paper`, absent live configuration has no
  effect.
- **No live broker adapter is implemented in this repository.** Adding one
  requires an explicit owner request, a new ADR and a security review.
- Paper and live use separate credential settings and separate base-URL
  constants; there is no shared "broker URL" setting.
- The current mode is shown permanently in the UI and returned by
  `/api/v1/system/info`.

## Alternatives considered

- **Boolean `LIVE=true`:** a single flag is too easy to set by accident.
- **Falling back to paper when live gates are missing:** hides a
  misconfiguration; an operator who asked for live must be told it did not start.

## Consequences

- Tests assert each gate independently and assert that no request can reach a
  non-paper broker host.

## Revisit when

The owner explicitly requests live trading.
