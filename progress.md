# Progress

**This file is the live status of the project.** Update it whenever a task is
finished, a blocker appears, or a session ends. A new contributor (human or model)
should be able to continue from this file alone, with `docs/BRAIN.md` for context.

- Last updated: 2026-11-17 (end of the first working session; handed off because
  the previous model hit its rate limit)
- Work branch: `claude/hopeful-einstein-krs00n` — **all work lives on this branch;
  `main` is still empty.**
- Handoff instructions for the next agent: `docs/HANDOFF.md`

---

## Current phase

- **Phase 0 — audit, research, decisions, environment: COMPLETE** (8/8 tests).
- **Phase 1 — canonical schemas, FastAPI, PostgreSQL, Redis, Next.js shell,
  health checks: IN PROGRESS** (12/38 acceptance tests passing).
  - Backend core (work items 1–6 of `docs/plan/phases.md` Phase 1): **code
    written**, but only the schema layer has automated tests so far.
  - Web app, Docker, `.env.example`, dependency scans (work items 7–9): **not
    started**.

---

## Finished work

### Phase 0 (2026-11-17)

Audit, dependency/licence verification, provider entitlement matrix, 11 ADRs,
architecture/risk/execution/security/runbook docs, phased plan, 274 acceptance
tests, brief preserved verbatim, `CLAUDE.md`/`AGENTS.md`/`docs/BRAIN.md`,
Lightweight Charts agent skills, `scripts/validate_brain.py`,
`scripts/tests_status.py`. Commit `980be4b`.

### Phase 1 so far (2026-11-17)

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

### Acceptance tests

| Phase | Total | Passing | Notes |
|-------|-------|---------|-------|
| 0 | 8 | 8 | `python3 scripts/validate_brain.py` |
| 1 | 38 | 12 | P1-UNIT-001…006, P1-UNIT-009, P1-PROP-001…002, P1-STATIC-001…003 |
| 2–15 | 228 | 0 | planned |

Run `python3 scripts/tests_status.py list --phase 1` for per-test status; tests
whose code exists but whose test is not written carry a note saying so.

---

## Unresolved problems

1. **Known defect — metrics route label.** For routers included with a prefix,
   `scope["route"].path` is the router-relative path (`/system/info`), so
   `http_requests_total{route=...}` lacks `/api/v1`. Cause: FastAPI 0.163 wraps
   included routers (`_IncludedRouter`). Fix in `apps/api/middleware.py`
   `route_template()` (e.g. prepend `scope["root_path"]`/router prefix, or read
   the full path template another way — inspect the installed FastAPI source
   first) and cover it with `P1-INT-005`.
2. **Backend code without automated tests** (listed above). Required by the
   definition of done before Phase 1 can close.
3. **Open compatibility items** that Phase 1 must still settle:
   C-01…C-03 (ESLint 10 + jsx-a11y + eslint-config-next + TypeScript 6.0.x;
   OpenAPI→TS generator), C-06 (can Docker pull images in this environment?),
   C-07 (Valkey vs redis-py 8.1.0) — `docs/architecture/dependency-decisions.md` §5.
   C-05 (httpx2) is settled: Starlette 1.10's `TestClient` requires `httpx2`
   (installed 2.16.2).
4. All other open questions: `docs/open-questions.md` (none blocks Phase 1).

---

## Next action

Continue **Phase 1** in this order. Do not start Phase 2.

1. Environment: start PostgreSQL and Redis, run `scripts/dev_db_setup.sh`
   (`docs/runbook.md` §2.2). Confirm the baseline: `uv sync`, `uv run pytest`
   (expect 143 passed), `uv run ruff check .`, `uv run mypy`, `uv run lint-imports`.
2. Write the missing backend tests, one ID per behaviour, using the existing code:
   - `tests/unit/test_settings.py` → P1-UNIT-007
   - `tests/unit/test_secrets_redaction.py` → P1-UNIT-008
   - `tests/unit/domain/test_no_naive_time.py` → P1-STATIC-004 (scan sources for
     `datetime.now(`/`utcnow(`/naive construction outside `SystemClock`)
   - `tests/integration/test_health.py` → P1-INT-001, P1-INT-002
   - `tests/integration/test_health_failures.py` → P1-FAIL-001, P1-FAIL-002
   - `tests/integration/test_migrations.py` → P1-INT-003
   - `tests/integration/test_correlation.py` → P1-INT-004
   - `tests/integration/test_metrics.py` → P1-INT-005 (fix the defect above first)
   - `tests/integration/test_system_info.py` → P1-INT-006
   - `tests/integration/test_errors.py` → P1-INT-007
   - `tests/integration/test_security_headers.py` → P1-SEC-002
   - `tests/contract/test_json_schema_export.py` + export script → P1-CONTRACT-002
   Integration tests need the `klowb_test` database; mark them
   `@pytest.mark.integration` (marker already registered in `pyproject.toml`).
3. `.env.example` + `tests/unit/test_env_example.py` → P1-SEC-003.
4. Web app (`apps/web`, pnpm workspace) → P1-WEB-*, P1-E2E-*, P1-CONTRACT-001.
   **Read the installed Next.js 16 package/docs before writing config** (OQ-T23);
   TypeScript 6.0.x, `@playwright/test` pinned to the environment's version.
5. Dockerfiles, `docker-compose.yml` (dev/test/prod profiles), `scripts/smoke.sh`
   → P1-SMOKE-001; dependency scans → P1-SEC-001.
6. Run every gate in `docs/runbook.md` §5, update `tests.json` via
   `scripts/tests_status.py`, update this file, write the Phase 1 adversarial
   self-review, commit, push.

---

## Commands used for verification

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
