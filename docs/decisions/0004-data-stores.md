# 0004 — Data stores

- Status: Accepted
- Date: 2026-11-17

## Context

Brief default: PostgreSQL for relational state, TimescaleDB optional when
justified, Redis for cache/pub-sub, DuckDB + Parquet for research/backtests.
License facts verified 2026-11-17: `asyncpg` is Apache-2.0, `psycopg` 3 is
LGPL-3.0-only; Redis ≤ 7.2.x is BSD-3-Clause, 7.4 is RSALv2/SSPLv1, 8+ is
tri-licensed RSALv2/SSPLv1/AGPLv3; Valkey is BSD-licensed and backed by the Linux
Foundation; TimescaleDB mixes Apache-2.0 with the Timescale License.

## Decision

- **PostgreSQL 16** is the system of record. Access through **SQLAlchemy 2.1
  async** with **asyncpg**; schema changes only through **Alembic** migrations.
  Money and prices are `numeric`; timestamps are `timestamptz` (UTC).
- Bars are stored in a plain table keyed `(instrument_id, provider, timeframe,
  ts)` with an index suited to range scans, designed so it can be partitioned by
  time later. **TimescaleDB is not adopted** until measurement shows plain
  PostgreSQL is insufficient.
- A **Redis-protocol server** provides latest-quote cache, pub/sub fan-out and
  rate-limit counters. It is **not** a system of record and the application must
  keep working (degraded) without it. Local development uses the installed Redis
  7.0.15 (BSD); the Compose file uses **Valkey** to keep the stack permissively
  licensed. Client: `redis-py` (MIT).
- **DuckDB + Parquet** for research datasets and backtest inputs/outputs.
  Datasets are immutable and identified by content hash (`data_snapshot_id`).

## Alternatives considered

- **psycopg 3:** capable, but LGPL — avoided when an Apache-2.0 driver exists.
- **TimescaleDB now:** premature; adds licensing nuance and operational weight.
- **Redis 8 image:** AGPL/RSAL/SSPL options are a design concern; Valkey avoids it.
- **SQLite for development:** would hide PostgreSQL-specific behaviour
  (`numeric`, `timestamptz`, concurrency).
- **Storing ticks in PostgreSQL:** not initially; bars and quarantined events
  only. Raw event capture goes to Parquet when needed.

## Consequences

- Integration tests need a real PostgreSQL (local service or Compose).
- Valkey compatibility with our Redis usage is proven by the integration tests
  (item C-07); fallback is a BSD-licensed Redis 7.2 image.

## Revisit when

Bar/tick volume makes range queries or retention management slow enough to
measure, or a managed database is chosen for deployment.
