# Architecture Decision Records

One file per decision: `NNNN-short-title.md`. Never rewrite history — to change a
decision, add a new ADR that supersedes the old one and update the old one's
status line.

Template:

```
# NNNN — Title
- Status: Accepted | Superseded by NNNN | Deprecated
- Date: YYYY-MM-DD
## Context
## Decision
## Alternatives considered
## Consequences
## Revisit when
```

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-modular-monolith-and-repository-layout.md) | Modular monolith and repository layout | Accepted |
| [0002](0002-python-toolchain.md) | Python toolchain and single root project | Accepted |
| [0003](0003-frontend-stack.md) | Frontend stack and version pins | Accepted |
| [0004](0004-data-stores.md) | Data stores | Accepted |
| [0005](0005-canonical-market-data-and-feed-quality.md) | Canonical market data model and feed quality | Accepted |
| [0006](0006-first-streaming-provider-kraken.md) | First streaming provider: Kraken WebSocket v2 | Accepted |
| [0007](0007-agent-orchestration.md) | Agent orchestration: in-house typed graph | Accepted |
| [0008](0008-backtest-and-execution-simulator.md) | Backtest and execution simulator: in-house | Accepted |
| [0009](0009-trading-safety-modes.md) | Trading safety modes and the live gate | Accepted |
| [0010](0010-background-work.md) | Background work: supervised asyncio tasks | Accepted |
| [0011](0011-in-house-analytics.md) | Indicators, performance analytics and sizing in-house | Accepted |
