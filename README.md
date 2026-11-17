# klowb

An institutional-style, free-first, multi-asset quantitative research and
day/swing-trading platform: US equities and ETFs, crypto spot and forex, with a
core designed to extend to futures and options.

> **Status: early development.** See [`progress.md`](progress.md) for exactly what
> exists today. This README describes the intended system; it does not claim that
> every feature below is built.

## What it is — and is not

- A disciplined research and trading workstation: deterministic calculations,
  explicit data provenance, realistic costs, reproducible backtests, transparent
  risk decisions, and AI research agents whose output is typed evidence, never an
  order.
- **Not** a system that predicts markets with certainty. Nothing here guarantees
  profit. Backtests and simulations are estimates with stated limitations.
- **Live trading is disabled by default.** The default mode is `research`. Paper
  trading is simulated. No live broker integration exists in this repository.

## Principles

1. Every price shown carries its **feed quality** (consolidated real-time,
   single-venue real-time, delayed, end-of-day, unofficial or simulated). Weaker
   data is never presented as stronger data.
2. UTC and timezone-aware timestamps internally; no future leakage in features,
   signals or backtests.
3. Bad market data is quarantined and surfaced, not silently fixed.
4. Research degrades gracefully when a provider fails; execution fails closed.
5. Every order passes one risk engine with hard limits and bounded sizing.

## Architecture (summary)

Modular monolith: a FastAPI backend (Python 3.13, Pydantic v2, asyncio), a Next.js
web app (React, strict TypeScript, Lightweight Charts, ECharts), PostgreSQL, a
Redis-protocol cache/pub-sub, and DuckDB + Parquet for research. Details:
[`docs/architecture.md`](docs/architecture.md).

## Run the Phase 1 workspace

From the repository root, select one Compose profile. Set `KLOWB_DB_PASSWORD`
and `KLOWB_MIGRATION_PASSWORD` to separate local alphanumeric secrets before
the first start. Keep them available for the lifetime of the database volume.

```sh
docker compose --profile dev up --build -d
scripts/smoke.sh
```

The web shell listens on loopback port 3000 and the research API on port 8000.
The shell displays system health, trading mode, and the feed-quality legend.
Other research areas are placeholders. See [the runbook](docs/runbook.md) for
private CA builds, profile isolation, local web development, and browser setup.

## Documentation

| Start here | |
|---|---|
| [`progress.md`](progress.md) | Current status and next action |
| [`docs/BRAIN.md`](docs/BRAIN.md) | Complete project context for anyone (or any AI model) taking over |
| [`docs/plan/phases.md`](docs/plan/phases.md) | Phased plan with acceptance tests |
| [`tests.json`](tests.json) | Every acceptance test and its status |

| Reference | |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Architecture, schemas, module boundaries |
| [`docs/architecture/dependency-decisions.md`](docs/architecture/dependency-decisions.md) | Dependencies, versions, licenses |
| [`docs/data-providers.md`](docs/data-providers.md) | Data providers, entitlements, adapter contract |
| [`docs/risk-model.md`](docs/risk-model.md) | Risk and position sizing |
| [`docs/execution-model.md`](docs/execution-model.md) | Orders, simulator, trading modes |
| [`docs/security.md`](docs/security.md) | Security controls |
| [`docs/runbook.md`](docs/runbook.md) | Setup, verification, operations |
| [`docs/decisions/`](docs/decisions/) | Architecture Decision Records |
| [`docs/open-questions.md`](docs/open-questions.md) | Open questions and assumed defaults |

## Verify the repository state

```bash
python3 scripts/validate_brain.py
```

Setup and run instructions are in [`docs/runbook.md`](docs/runbook.md) and are
marked as verified only once they have actually been executed.

## Third-party notices

Financial charts use [TradingView Lightweight Charts™](https://github.com/tradingview/lightweight-charts)
(Apache-2.0), which requires attribution to TradingView. Full dependency and
license information: [`docs/architecture/dependency-decisions.md`](docs/architecture/dependency-decisions.md).

## License

Not yet chosen by the owner (see `docs/open-questions.md`, B-02).
