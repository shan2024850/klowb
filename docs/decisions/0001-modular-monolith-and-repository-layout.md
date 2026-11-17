# 0001 — Modular monolith and repository layout

- Status: Accepted
- Date: 2026-11-17

## Context

The repository was empty (two commits: an initial README and its deletion). The
brief sets an architectural default — modular monolith, Next.js + FastAPI,
PostgreSQL, Redis, DuckDB/Parquet, Docker Compose — and proposes a directory
structure, to be adapted only if the existing repository strongly suggests
something better. Nothing existed to suggest otherwise.

## Decision

- Build a **modular monolith**: one FastAPI backend process, one Next.js web
  process, PostgreSQL, a Redis-protocol server, and files for research.
- Adopt the brief's layout (`apps/`, `packages/`, `services/`, `libs/`, `data/`,
  `tests/`, `docs/`) with these additions: `migrations/` (Alembic), `scripts/`,
  Playwright specs inside `apps/web/e2e/`, and `packages/ui/` deferred until a
  second consumer exists.
- Python code is **one project** with import roots `apps.api`, `services.*`,
  `libs.*`. Domain boundaries are enforced with `import-linter` layer contracts
  (`docs/architecture.md` §3) rather than by separate distributions.
- Services communicate only through types in `libs.schemas` and an event-bus
  abstraction, so any domain can later be moved behind a network boundary.

## Alternatives considered

- **uv workspace with one distribution per service.** Stronger isolation, but
  nine-plus `pyproject.toml` files and inter-package version management for no
  present benefit. Import contracts give the same guarantee at near-zero cost.
- **Microservices from the start.** Rejected by the brief ("do not deploy Kafka or
  microservices without measured need").
- **Single `src/klowb/` package.** Cleaner import names, but diverges from the
  structure the brief proposes without a strong reason.

## Consequences

- Top-level import names (`apps`, `services`, `libs`) are generic; this is an
  application, not a published library, so name collisions are not a practical
  concern. The project is not packaged for distribution.
- Boundary violations fail CI instead of relying on review.

## Revisit when

A domain needs independent scaling, a different release cadence or a different
runtime — extract it then, using the existing contracts.
