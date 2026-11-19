# 0008 — Backtest and execution simulator: in-house

- Status: Accepted (to be re-confirmed at the start of Phase 9)
- Date: 2026-11-17

## Context

The brief allows either "an event-driven simulator or … a carefully selected
engine" and lists the required behaviours (bid/ask, order types, partial fills,
rejections, costs, participation, latency, market hours, corporate actions,
borrow/funding, gap-through-stop, stale orders, lookahead tests, walk-forward,
persistence of run metadata). Engines considered (verified 2026-11-17):

| Engine | License | Fit |
|--------|---------|-----|
| QuantConnect Lean | Apache-2.0 | Mature, but a C#/.NET engine with its own data formats and order model. |
| nautilus_trader | LGPL-3.0-or-later | High-fidelity, Python API over a Rust core; in a v1→v2 transition with breaking changes possible. |
| freqtrade | GPL-3.0 | An application; GPL incompatible with importing into this codebase. |
| hummingbot | Apache-2.0 | Market-making application framework. |
| qlib | MIT | Research workflow, not an execution simulator. |

The platform's central safety property is that **backtest, paper and (gated) live
trading share one order model, one risk engine and one cost model**. Adopting an
external engine means either adopting its domain model everywhere or maintaining a
translation layer on the most safety-critical path.

## Decision

Build an **in-house event-driven simulator** (`services/execution/sim`,
`services/backtesting`) on the canonical schemas, the shared `Clock`, the
calendars and the shared cost model, as specified in `docs/execution-model.md`.

## Alternatives considered

- **nautilus_trader** is the strongest alternative and remains the named fallback.
  Reasons not to adopt now: LGPL (a design concern per the brief), API churn
  during its v2 transition, and the domain-model duplication above.
- **Lean:** second runtime and toolchain.

## Consequences

- We must implement and test fill logic ourselves; the acceptance tests in Phase 9
  (`P9-*`) are the specification.
- Fidelity is bounded by the data we have (bars and top-of-book, not full depth
  or queue position); reports must state this.

## Revisit when

At Phase 9 kickoff (compare against nautilus_trader's then-current release and
license); or if required fidelity (order-book queue modelling, exchange-specific
matching rules) exceeds what is reasonable to maintain in-house.
