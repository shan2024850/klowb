# Progress

**This file is the live status of the project.** Update it whenever a task is
finished, a blocker appears, or a session ends. A new contributor (human or model)
should be able to continue from this file alone, with `docs/BRAIN.md` for context.

- Last updated: 2026-11-17 (Codex Phase 1 backend checkpoint)
- Work branch: `claude/hopeful-einstein-krs00n` — **all work lives on this branch;
  `main` is still empty.**
- Handoff instructions for the next agent: `docs/HANDOFF.md`

### Codex baseline (2026-11-17)

Fetched the work branch at 11fc401. Brain checks: 8/8. Tracker: 20/274.
Host version probes: Python 3.12.14, uv 0.13.6, Node 24.22.1, pnpm 11.25.0,
Docker 29.9.2. Bare `uv sync` failed on the read-only home cache. With
`export UV_CACHE_DIR=/tmp/klowb-uv-cache`, uv selected system CPython 3.13.5.
`uv sync && uv run pytest && uv run ruff check . && uv run mypy && uv run lint-imports`
passed (143 cases, 59 mypy source files, two import contracts).
Host psql, redis-server and sudo absent; host `scripts/dev_db_setup.sh` failed.
Started postgres:16 and redis:7 containers (klowb-pg and klowb-redis) with ports
5432 and 6379 published on loopback. `docker exec -i klowb-pg bash -s < scripts/dev_db_setup.sh`
created the dev role and both databases. `docker exec klowb-redis redis-cli ping` returned PONG.

---

## Current phase

- **Phase 0 — audit, research, decisions, environment: COMPLETE** (8/8 tests).
- **Phase 1 — canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell,
  health checks: IN PROGRESS** (27/38 acceptance tests passing).
  - Backend and environment example tested. Web, deployment, and audits outstanding.
  - Overall: 35/274 passing. Three Phase 1 browser cases are blocked.

---

## Finished work

### Phase 0 (2026-11-17)

Audit, dependency/licence verification, provider entitlement matrix, 11 ADRs,
architecture/risk/execution/security/runbook docs, phased plan, 274 acceptance
tests, brief preserved verbatim, `CLAUDE.md`/`AGENTS.md`/`docs/BRAIN.md`,
Lightweight Charts agent skills, `scripts/validate_brain.py`,
`scripts/tests_status.py`. Commit `980be4b`.

### Phase 1 at the original handoff (historical)

Each line says whether it is **tested** (automated test exists and passes),
**smoke-checked** (run by hand once, no automated test yet) or **untested**.

| Area | Files | State |
|------|-------|-------|
| Python project, pinned deps, tool config | `pyproject.toml`, `uv.lock` | ruff, mypy strict, pytest, import-linter configured; all pass |
| Domain enums, clock, symbol rules | `libs/domain/enums.py`, `clock.py`, `symbols.py` | **tested** (via schema tests) |
| Canonical schemas | `libs/schemas/types.py`, `market.py`, `instrument.py`, `hashing.py`, `system.py` | **tested**: 143 tests in `tests/unit/schemas/`, `tests/property/` |
| Structured logging + redaction | `libs/observability/logging.py`, `redaction.py` | smoke-checked; **no tests** |
| Correlation-ID middleware | `libs/observability/correlation.py` | smoke-checked; **no tests** |
| Prometheus metrics | `libs/observability/metrics.py` | smoke-checked; **no tests**; known defect below |
| DB / cache clients, table base, audit table | `libs/storage/database.py`, `cache.py`, `base.py`, `audit.py` | smoke-checked; **no tests** |
| Market-data tables | `services/market_data/tables.py` | migration round-trip checked by hand |
| App settings with trading-safety gates | `apps/api/settings.py` | smoke-checked (live refused); **no tests** |
| Error envelope, middleware, health, routers, app factory | `apps/api/errors.py`, `middleware.py`, `health.py`, `deps.py`, `routers/health.py`, `routers/system.py`, `main.py`, `tables.py`, `version.py` | smoke-checked; **no tests** |
| Alembic + initial migration | `alembic.ini`, `pyproject.toml [tool.alembic]`, `migrations/env.py`, `migrations/versions/20261117_dc947b200818_initial_schema.py` | upgrade → downgrade → upgrade and `alembic check` verified by hand; **no test** |
| Local DB setup script | `scripts/dev_db_setup.sh` | run successfully (idempotent) |
| Test factories | `tests/factories.py` | used by tests |

Manual smoke results (2026-11-17, `TestClient`, local PostgreSQL 16 + Redis 7):
`/healthz` 200; `/readyz` 200 with postgres+redis `up`; unreachable DB →
`/readyz` 503 `unavailable` while `/healthz` stays 200; `/api/v1/system/info`
200 with `trading_mode=research`, `live_trading_available=false`; unknown route →
404 in the standard envelope with the request's correlation id; security headers
present; `/metrics` exposes `http_requests_total` and `dependency_up`;
`Settings(trading_mode="live")` raises `LiveTradingRefused`.

### Phase 1 backend checkpoint (2026-11-17)

Completed steps 2 and 3. Added tests for settings, redaction, time policy,
liveness/readiness and dependency failures, migration round trip in a private
transactional schema, correlation, metrics, system info, errors, security
headers/CORS, canonical JSON exports and the environment example. Fixed the
prefix-aware route template and prevented opaque nested values past the redaction
depth limit from reaching log output. Generated six JSON contracts.

## Unresolved problems

The metrics defect is fixed. The first regression run failed on the prefix;
the same test then passed. Browser preflight conflicts with the documented
environment: preinstalled Playwright is 1.62.1, the expected headless executable
is absent, and the required 1.63.0 browser installation is not provisioned.
A system chromium binary exists. The project prohibits downloading a browser
or substituting a runner version. See docs/open-questions.md. Frontend
compatibility, the integrated Compose smoke test and dependency scans remain open.

**Browser blocker resolved (2026-11-17, owner-side review):** the "never run
`playwright install`" rule was a fact about the first session's container,
mis-stated as a project rule. ADR-0012 replaces it: pin `@playwright/test`
1.63.0 in `apps/web/package.json` and install its matching Chromium with
`pnpm --filter @klowb/web exec playwright install chromium`. P1-E2E-001…003 are
back to `planned`.

## Next action

Resume Phase 1 step 4 now (browser baseline reconciled by ADR-0012): add
`@playwright/test` 1.63.0 to `apps/web`, run
`pnpm --filter @klowb/web exec playwright install chromium` (record blocked with
the error only if the download itself fails).
Read installed Next 16 docs, scaffold apps/web and generated API types, run the
web/static, component, contract and browser gates. Then complete steps 5–6
(Compose, audits, full-stack smoke, self-review). Phase 2 has not started.

### Codex verification commands (2026-11-17)

- `uv run python -m scripts.export_schemas` generated the snapshots.
- `uv run pytest`: 164 passed, including service-backed cases.
- `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports`:
  clean, 104 formatted files, 74 typed source files, two import contracts kept.
- `node -p "require('playwright/package.json').version"`: 1.62.1.
  Default `require('playwright').chromium.launch()` failed (headless shell missing).
- Tracker updated via `scripts/tests_status.py set`. No web, Docker stack smoke
  or audit result is claimed. Test services ran in local Docker containers.
- Baseline commands and the Docker database bootstrap are recorded above.

## Commands used for verification in the original environment

Executed on 2026-11-17 in the development environment.

```bash
# Phase 0
python3 scripts/validate_brain.py                       # 8/8 checks passed

# Phase 1 environment
service postgresql start && redis-server --daemonize yes --save '' --appendonly no
scripts/dev_db_setup.sh                                 # creates role klowb, dbs klowb + klowb_test
uv sync                                                 # Python 3.13.18, deps per uv.lock

# Phase 1 gates that exist so far
uv run ruff check . && uv run ruff format --check .    # All checks passed / 88 files formatted
uv run mypy                                             # Success: no issues found in 59 source files
uv run lint-imports                                     # Contracts: 2 kept, 0 broken
uv run pytest                                           # 143 passed

# Migrations (manual)
export DATABASE_URL=postgresql+asyncpg://klowb:klowb@localhost:5432/klowb_test
uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head
uv run alembic check                                    # No new upgrade operations detected.

# Manual API smoke: create_app(Settings()) with fastapi.testclient.TestClient,
# GET /healthz, /readyz, /api/v1/system/info, /metrics, /nope; then a second app
# with an unreachable DATABASE_URL and REDIS_URL="" (results under "Finished work").
```

---

## Adversarial self-review

### Phase 0

- Provider facts carry V/P/U verification status; unverified items default to the
  conservative choice and are listed in `docs/research/verification-log.md` §2.
- Not verified: repository last-commit dates, market-data redistribution terms,
  several free-tier details. Re-check in the phase that uses them.
- Runbook tags only executed commands as verified.

### Phase 1 (partial, at handoff)

- **Do not over-trust the backend code that has no tests.** It was smoke-checked
  once by hand; edge cases (redaction of nested secrets, CORS validation, error
  boundary after a started response, Redis disabled path) are unproven.
- A real defect was already found by testing: `str(Decimal("0.00000001"))` is
  `1E-8`; JSON serialisation now uses fixed-point (`decimal_to_plain_string`)
  with a regression test. Expect similar issues in untested code.
- `libs/schemas` rejects binary floats on purpose; adapters must parse provider
  JSON with `parse_float=Decimal` (`libs.schemas.hashing.parse_json_exact`).
